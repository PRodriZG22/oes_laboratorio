# Plan de pruebas y despliegue

## Preparación y evidencias

La sección 8 de la guía exige seis pruebas. Se documenta tanto el procedimiento manual como una ejecución repetible con `unittest` y `streamlit.testing.v1.AppTest`. No se agrega pytest a las dependencias de producción. Las pruebas usan bases temporales mediante `OES_DB_PATH`; la base entregada mantiene tres ejemplos.

Registrar por prueba: identificador, entrada, procedimiento, resultado esperado, resultado observado y evidencia. Guardar resultados reales en `evidencias/RESULTADOS_PRUEBAS.md`. Una captura del dashboard es evidencia visual complementaria, no sustituto de aserciones ni de haber agregado una noticia real.

## P1 Carga idempotente

1. Crear una copia de trabajo vacía; no borrar una base que contenga trabajo del usuario.
2. Ejecutar `python preparar_datos.py` dos veces contra esa misma base.
3. Consultar cantidad de filas y cantidad de URLs distintas.
4. Comparar los siete campos con la semilla de la guía.

Esperado: **3 filas, 3 URLs**, ninguna repetida ni campos originales alterados. La segunda ejecución informa cero altas. La auditoría de los ejemplos continúa didáctica y sin responsable.

Evidencia: salida de ambas cargas y consulta SQL. No usar `MAX(id)` como número de noticias, porque SQLite puede tener saltos de identificador.

## P2 Filtro Universidad pública

1. Abrir la app con los tres ejemplos y restablecer filtros.
2. Dejar únicamente `Universidad pública`.
3. Mantener búsqueda vacía y fechas que cubran 2026-11-05–2026-11-06.
4. Revisar tabla, KPIs y barras.

Esperado: solo **UNMSM**, con una noticia, una institución y una categoría. La URL es `https://www.unmsm.edu.pe/` y su estado es didáctico.

## P3 Búsqueda PUCP

1. Restablecer categorías y fechas.
2. Ingresar `PUCP` en Buscar título o institución.
3. Revisar la selección y los indicadores.

Esperado: **una fila**, institución PUCP, métricas 1/1/1. Probar también minúsculas como control adicional.

## P4 Término inexistente

1. Restablecer filtros.
2. Buscar `termino_inexistente_oes_987654`.
3. Revisar aviso, tabla y botones de descarga.

Esperado: **0 noticias**, KPIs 0/0/0, aviso sin resultados, ninguna excepción. El CSV vacío conserva encabezados; el PDF es válido y explica la ausencia de coincidencias.

## P5 Exportación CSV

1. Filtrar Universidad pública para obtener UNMSM.
2. Pulsar Exportar CSV.
3. Abrir con Excel o lector CSV utilizando UTF-8 con BOM.
4. Comprobar encabezados, una fila, URL exacta, categoría acentuada y auditoría.
5. Repetir con una selección sin resultados.

Esperado: BOM `EF BB BF`, sin columna de índice artificial, una fila UNMSM en el primer archivo y solo encabezados en el segundo. El archivo corresponde a los filtros actuales. Un texto que pudiera ejecutarse como fórmula se exporta neutralizado.

La prueba automática inspecciona los bytes del mismo generador usado por el botón; la revisión visual comprueba que el control de descarga se presenta en la interfaz.

## P6 Alta real verificada

1. Abrir una **nota concreta en una fuente oficial**, con titular y fecha visibles. No utilizar los portales genéricos de la semilla, una URL inventada ni un marcador de posición.
2. Registrar en la evidencia el enlace consultado, fecha de consulta, titular y fecha publicados, fuente y resumen propio. La fixture de prueba solo se fija después de revisar el original.
3. En una base temporal con tres ejemplos, restablecer filtros y anotar contador 3.
4. Completar todos los campos del formulario y el responsable declarado.
5. Intentar guardar sin confirmación; comprobar que continúa en 3.
6. Marcar la confirmación después de revisar el original y guardar.
7. Comprobar contador **4**, ficha registrada, URL directa intacta, captura no vacía, responsable y estado `verificado`.
8. Intentar repetir la URL; comprobar que continúa en 4.

Esperado: aumento de una fila únicamente tras la confirmación. La prueba de integración puede reproducir el envío del formulario con `AppTest`; eso verifica la mecánica, no autentica a una persona ni vuelve a comprobar una fuente que haya cambiado. El origen revisado y la limitación quedan documentados.

## Controles adicionales

| Control | Resultado esperado |
| --- | --- |
| Primera visita sin `oes.db` | Se crea automáticamente con tres ejemplos |
| Archivo de cero bytes o tabla vacía | Se recupera la demostración sin error |
| Tabla no vacía con noticias reales | No se agregan ejemplos automáticamente |
| Rango de un día | Incluye fechas iguales a ambos extremos |
| Rango incompleto, invertido o fuera de datos | Aviso o cero filas sin excepción |
| Ninguna categoría seleccionada | Cero filas y tres métricas cero |
| Búsqueda `.*` o corchetes | Se busca literalmente, sin regex |
| Campos vacíos, URL sin HTTP(S), dominio inválido o credenciales | Alta rechazada; base intacta |
| URL de portada en formulario | Solicitar URL directa; no simular verificación |
| Fecha imposible o futura | Alta rechazada |
| Restricciones SQLite | URL duplicada y verificado sin responsable no se admiten |
| Migración de tabla original | Se conservan filas; ejemplos didácticos y otros pendientes |
| Base corrupta o incompatible | Mensaje de revisión, sin borrado automático |
| PDF con selección o vacío | Documento válido, URLs, auditoría y filtros presentes |
| Importación de módulos | No inicia servidor ni carga datos por efecto lateral |
| Proceso Streamlit real | Endpoint de salud responde y dashboard abre |

## Comandos locales Windows

Desde la raíz del proyecto:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe preparar_datos.py
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell. Abrir la URL local que indique Streamlit, normalmente `http://localhost:8501`. En Linux/macOS sustituir el intérprete por `.venv/bin/python`.

## Preparación de GitHub

1. Revisar el inventario y ejecutar las pruebas.
2. Confirmar que `.gitignore` excluye `.venv/`, `__pycache__/`, archivos transitorios, secretos y bases de prueba; **no excluye `oes.db`**.
3. Crear un repositorio en GitHub. No subir notas privadas, credenciales ni nombres de verificadores sin necesidad.
4. Ejecutar `git init`, `git add .`, `git commit -m "Prototipo académico OES"` y `git branch -M main`.
5. Copiar desde GitHub el comando real `git remote add origin ...` y ejecutar `git push -u origin main`. No se proporciona un remoto ficticio que parezca real.
6. Comprobar que `app.py`, `preparar_datos.py`, `requirements.txt`, configuración y recursos locales estén en el repositorio.

La base inicial puede subirse porque contiene ejemplos públicos. También puede omitirse: el arranque la crea. Subir `oes.db` no convierte futuras altas en almacenamiento persistente de Cloud.

## Streamlit Community Cloud

1. Ingresar a [Streamlit Community Cloud](https://share.streamlit.io/) y conectar la cuenta GitHub con acceso al repositorio.
2. Elegir **Create app**, seleccionar repositorio, rama `main` y archivo principal **`app.py`**.
3. En **Advanced settings**, escoger una versión compatible. Se recomienda Python **3.12** para un entorno conservador; el código utiliza sintaxis compatible con 3.11 o posterior. Verificar las versiones disponibles en el selector al desplegar.
4. Mantener `requirements.txt` en raíz. No agregar `sqlite3` a pip ni claves de APIs.
5. Pulsar Deploy y revisar los logs de instalación y arranque.
6. Comprobar tres registros, P2–P5 y descarga PDF. P6 se realiza con una nota oficial y revisión real, conservando copia fuera del disco efímero.
7. Reiniciar la app de prueba y verificar que el arranque funciona con o sin la base incluida. No usar esta prueba como garantía de persistencia.

No se afirma haber publicado hasta disponer de URL de despliegue y haberla comprobado. No se requiere crear una cuenta externa ni publicar el repositorio para validar el código local.

## Conservación y operación

Las altas manuales en Cloud pueden perderse después de un reinicio o despliegue. Descargar CSV del conjunto completo con frecuencia y mantener respaldos fuera de la instancia; para operación institucional usar una base persistente. No se implementan autenticación, autorización, importación de respaldos ni historial de cambios en este MVP.

## Referencias verificadas

- Guía adjunta, secciones 4, 8–10.
- [Organización de archivos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).
- [Dependencias de la app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
- [Despliegue y selección de Python](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
- [Pruebas con AppTest](https://docs.streamlit.io/develop/api-reference/app-testing).
