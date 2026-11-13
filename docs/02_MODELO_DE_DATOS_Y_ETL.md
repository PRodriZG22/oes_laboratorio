# Modelo de datos y ETL

## Modelo físico

La sección 5 de la guía propone las entidades institución, fuente y noticia, pero simplifica la práctica con una única tabla desnormalizada `noticias` en `oes.db`. Esto permite reproducir las pruebas sin joins. Institución y fuente son textos; no se simula una normalización inexistente.

| Campo | Tipo SQLite | Nulabilidad y restricciones | Significado |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador interno; no implica orden cronológico |
| `titulo` | TEXT | NOT NULL, texto no vacío | Titular original o ejemplo de la guía |
| `institucion` | TEXT | NOT NULL, texto no vacío | Entidad a la que corresponde la ficha |
| `categoria` | TEXT | NOT NULL, catálogo permitido | Tipo institucional |
| `fuente` | TEXT | NOT NULL, texto no vacío | Nombre de la fuente consultada |
| `fecha` | TEXT | NOT NULL, formato ISO `AAAA-MM-DD` | Fecha de publicación, no de captura |
| `url` | TEXT | NOT NULL, UNIQUE, HTTP(S) | URL exacta del portal didáctico o de la nota real |
| `resumen` | TEXT | NOT NULL, texto no vacío | Síntesis propia, sin atribuir afirmaciones inexistentes |
| `fecha_de_captura` | TEXT | NOT NULL, predeterminado UTC | Instante de incorporación `AAAA-MM-DDTHH:MM:SSZ` |
| `verificado_por` | TEXT | NULL para ejemplos; obligatorio para verificados | Responsable declarado, sin autenticación |
| `estado_de_verificacion` | TEXT | NOT NULL, CHECK de estados | `didactico`, `pendiente` o `verificado` |

Catálogo de categorías: `Ente rector`, `Universidad pública`, `Universidad privada`, `Instituto de educación superior`, `Otro`. Es una clasificación operativa de la práctica; no certifica la naturaleza jurídica de cada entidad.

## Esquema de referencia

```sql
CREATE TABLE IF NOT EXISTS noticias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL CHECK(length(trim(titulo)) > 0),
    institucion TEXT NOT NULL CHECK(length(trim(institucion)) > 0),
    categoria TEXT NOT NULL CHECK(categoria IN (
        'Ente rector', 'Universidad pública', 'Universidad privada',
        'Instituto de educación superior', 'Otro'
    )),
    fuente TEXT NOT NULL CHECK(length(trim(fuente)) > 0),
    fecha TEXT NOT NULL CHECK(
        fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(fecha) IS NOT NULL AND date(fecha) = fecha
    ),
    url TEXT NOT NULL UNIQUE CHECK(
        url LIKE 'https://%' OR url LIKE 'http://%'
    ),
    resumen TEXT NOT NULL CHECK(length(trim(resumen)) > 0),
    fecha_de_captura TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    verificado_por TEXT,
    estado_de_verificacion TEXT NOT NULL DEFAULT 'pendiente'
        CHECK(estado_de_verificacion IN ('didactico', 'pendiente', 'verificado')),
    CHECK(estado_de_verificacion <> 'verificado' OR
        (verificado_por IS NOT NULL AND length(trim(verificado_por)) > 0))
);
CREATE INDEX IF NOT EXISTS idx_noticias_fecha ON noticias(fecha);
CREATE INDEX IF NOT EXISTS idx_noticias_categoria ON noticias(categoria);
```

SQLite aporta controles de estructura. Python valida además fechas de calendario, longitudes y estructura de URL antes de cada alta. La fecha de captura se registra en UTC para comparar instantes; la fecha de publicación se conserva como día civil, sin desplazarla de zona horaria.

Si se detecta una tabla antigua de la guía con los ocho campos originales, se añaden los tres campos de auditoría sin eliminar filas: los ejemplos exactos se marcan didácticos y los demás registros se mantienen pendientes, nunca verificados por inferencia. Una migración compatible puede tener menos restricciones físicas que el esquema nuevo; la validación de altas se mantiene y se documenta. Un esquema desconocido o URLs duplicadas se rechaza con un mensaje de respaldo/revisión, sin borrar información.

## Contrato de inicialización

`inicializar_base(ruta=None, cargar_ejemplos=True)` crea directorio y esquema compatibles y ejecuta una transacción. Como script, `python preparar_datos.py` carga los ejemplos usando `INSERT OR IGNORE`; ejecutarlo dos veces no crea duplicados ni cambia auditorías preexistentes. Debe informar ruta, total y nuevas filas.

`app.py` prepara el esquema al arrancar, comprueba si faltan datos e invoca la misma inicialización con carga de ejemplos cuando la base está ausente o la tabla está vacía. No debe depender de que alguien ejecute antes el script. Una tabla no vacía con noticias reales no recibe ejemplos automáticamente.

## Carga inicial exacta

Los siguientes siete campos se copian literalmente de la guía. No se sustituye ninguna URL por una dirección inventada ni se rastrean portales para ampliar la semilla.

| Campo | Registro 1 | Registro 2 | Registro 3 |
| --- | --- | --- | --- |
| titulo | Ejemplo: convocatoria de becas | Ejemplo: actividad de investigación | Ejemplo: programa académico |
| institucion | PRONABEC | UNMSM | PUCP |
| categoria | Ente rector | Universidad pública | Universidad privada |
| fuente | Portal institucional (ejemplo) | Portal institucional (ejemplo) | Portal institucional (ejemplo) |
| fecha | 2026-11-06 | 2026-11-06 | 2026-11-05 |
| url | https://www.pronabec.gob.pe/ | https://www.unmsm.edu.pe/ | https://www.pucp.edu.pe/ |
| resumen | Registro didáctico: verificar nota original. | Registro didáctico: verificar noticia original. | Registro didáctico: verificar noticia original. |

Auditoría de los tres: captura en UTC al insertar, `verificado_por = NULL`, `estado_de_verificacion = 'didactico'`. Fechas y titulares no se presentan como hechos comprobados.

## ETL de ejemplos

1. **Extracción:** leer la constante inmutable con los tres registros transcritos.
2. **Transformación:** mantener literalmente los siete valores; incorporar estado didáctico y captura automática.
3. **Carga:** `executemany` parametrizado con `INSERT OR IGNORE` dentro de una transacción.
4. **Control:** contar filas y URLs distintas; en una base nueva ambos resultados deben ser tres. El identificador puede tener saltos y no es un contador de noticias.

## Captura de una noticia real

1. Una persona abre una nota oficial, comprueba titular, fecha, institución y URL directa.
2. Redacta un resumen propio, consigna fuente y su identificador de revisión.
3. El formulario exige confirmación explícita de haber revisado la nota. No se registra por defecto.
4. Se recortan espacios exteriores y se validan campos obligatorios y límites de longitud.
5. La URL debe empezar por `http://` o `https://`, tener dominio válido, no contener credenciales ni espacios y apuntar a una ruta o consulta concreta. No se accede automáticamente al destino: la validación es sintáctica y la revisión de contenido es humana.
6. Se rechazan fechas imposibles o posteriores al día actual de Lima.
7. Se inserta con parámetros, estado `verificado`, responsable y captura. Las URLs duplicadas no se sobrescriben y se informa al usuario.

`UNIQUE(url)` utiliza igualdad textual. No detecta por sí sola versiones con parámetros de seguimiento, redirecciones, cambios de mayúsculas en rutas o notas republicadas; se recomienda copiar la URL canónica. No se alteran automáticamente rutas o consultas que podrían identificar recursos distintos.

## Calidad, preservación y evolución

- La aplicación lee fechas con conversión controlada y evita excepciones al filtrar.
- Las exportaciones incluyen los tres campos de auditoría y permiten distinguir ejemplos de noticias verificadas.
- No hay borrado ni edición en la interfaz inicial; se evita modificar evidencia histórica sin un registro de cambios.
- Para respaldo completo local se debe cerrar la aplicación y copiar `oes.db`; el CSV es una exportación lógica de la selección, no una copia binaria de la base.
- Para producción: normalizar catálogos, agregar usuarios autenticados, historial de cambios, deduplicación editorial, pruebas de restauración y almacenamiento persistente.

## Referencias

Guía adjunta, secciones 5, 7–9. [Python sqlite3 y consultas con parámetros](https://docs.python.org/3/library/sqlite3.html). [Restricciones de SQLite](https://www.sqlite.org/lang_createtable.html).
