# Diseño del dashboard Streamlit

## Objetivo de interacción

La interfaz permite identificar novedades, revisar su procedencia y descargar evidencia. La página principal se llama **Observatorio de Educación Superior** y lleva un subtítulo de prototipo académico. Se utiliza una composición ancha, fondo claro, tipografía legible, azul profundo y acento turquesa. La distinción didáctico/verificado se expresa con texto, no solamente mediante color.

## Organización

| Zona | Elementos | Comportamiento |
| --- | --- | --- |
| Encabezado | Nombre, propósito y aviso metodológico | Explica que los ejemplos enlazan a portales y no son noticias verificadas |
| Barra lateral superior | Filtros, categoría, búsqueda y fechas | Selección múltiple con todas las categorías activas inicialmente |
| Barra lateral inferior | Formulario de registro verificable en sección desplegable | Campos propios, fecha, URL, responsable y casilla de verificación sin activar |
| Resumen principal | Tres tarjetas KPI | Noticias, instituciones y categorías del conjunto filtrado |
| Análisis | Barras por categoría | Solo categorías presentes, conteos exactos, sin inferir calidad |
| Consulta | Tabla y detalle de una ficha | URL clicable, fuente, fecha y estado visibles; auditoría y resumen consultables |
| Salidas | Botones CSV y PDF | Descargan exactamente la selección actual |
| Pie o sección informativa | Alcance, metodología y conservación | Explica almacenamiento efímero y significado de verificación declarada |

No se incluyen nombres, logos ni recursos visuales del OES comercial. El diseño es original y no depende de una red externa para cargar recursos.

## Arranque

1. Configurar título, icono y disposición con `st.set_page_config`.
2. Resolver `oes.db` junto al script, salvo `OES_DB_PATH` explícito.
3. Asegurar esquema y leer el número de filas.
4. Si la base falta o está vacía, ejecutar la carga didáctica automáticamente.
5. Leer con `pandas.read_sql_query`, orden descendente por fecha e identificador.
6. Si ocurre un error de almacenamiento, mostrar instrucción de revisión/respaldo y detener solo la presentación; no borrar la base.

## Filtros

| Control | Regla | Estado límite |
| --- | --- | --- |
| Categoría | `multiselect` con categorías existentes; unión entre opciones | Lista vacía produce cero resultados |
| Buscar título o institución | Recortar extremos; búsqueda literal, sin distinguir mayúsculas, `regex=False` | Vacío no restringe; caracteres `.*[]` no se ejecutan como expresión regular |
| Rango de publicación | Dos extremos inclusivos; por defecto cubre mínimo–máximo de los datos | Un extremo incompleto o inicio posterior al fin muestra aviso y cero filas |
| Restablecer filtros | Regresar al conjunto completo | Recalcula opciones y límites con datos actuales |

Los tres filtros se combinan con AND. Se utiliza la fecha de publicación, no la de captura. El nuevo registro, al guardarse, restablece filtros y fechas para quedar visible; se comunica al usuario.

## KPIs y gráfico

`Noticias = len(filtrado)`, `Instituciones = nunique(institucion)`, `Categorías = nunique(categoria)`. Todos dependen del mismo DataFrame y no de la tabla completa.

| Estado de prueba | Noticias | Instituciones | Categorías |
| --- | ---: | ---: | ---: |
| Base inicial sin filtros | 3 | 3 | 3 |
| Solo Universidad pública | 1 | 1 | 1 |
| Búsqueda PUCP | 1 | 1 | 1 |
| Término inexistente | 0 | 0 | 0 |

Las barras representan `value_counts` por categoría. Se rotulan como distribución de **registros**, sin equivalencias con prestigio, impacto o calidad universitaria. Sin resultados se omite el gráfico y aparece un aviso claro.

## Tabla, enlaces y trazabilidad

La tabla conserva encabezados aunque no haya filas. Se muestran al menos fecha, institución, categoría, título, fuente, URL y estado. `st.column_config.LinkColumn` convierte URL en enlace; la URL completa permanece visible para revisar el dominio y no se construye HTML a partir de contenido ingresado.

La auditoría también está disponible en tabla/exportación. Un detalle seleccionado permite leer el resumen completo, captura UTC y responsable sin truncar información en tarjetas pequeñas. Los títulos de ejemplos mantienen el prefijo `Ejemplo:` y el estado se presenta como **Didáctico · no verificado**.

## Formulario lateral

Campos: título, institución, categoría, fuente oficial, fecha de publicación, URL directa, resumen propio y verificado por. La fecha predeterminada es el día actual en Lima, con validación también en servidor. Los identificadores de verificación son declarativos; no hay autenticación ni certificación de identidad.

La casilla dice: **Confirmo que abrí la URL directa y comprobé el titular, la fecha y el resumen con la fuente original.** Su valor inicial es falso. La función de registro vuelve a exigir esta confirmación, aunque se invoque fuera del formulario.

Al guardar:

1. Validar todos los campos y la URL según `02`.
2. Rechazar sin escribir si falta revisión, existe un campo inválido o la fecha es futura.
3. Insertar con estado verificado y captura UTC; ante URL repetida, avisar sin actualizar.
4. Confirmar éxito, restablecer filtros y recargar la consulta. El contador general aumenta en uno.

El formulario no descarga el enlace ni infiere veracidad con IA. No se autocompletan hechos, fechas ni enlaces.

## CSV

- Nombre sugerido `oes_resultados.csv` y MIME `text/csv`.
- Codificación `utf-8-sig`, encabezado y sin índice pandas.
- Columnas: identificación, siete campos editoriales y tres campos de auditoría.
- Se conservan acentos, URL y estado de verificación.
- Cero resultados permite descargar únicamente encabezados.
- Si un valor comienza con caracteres interpretables como fórmulas por hojas de cálculo, se neutraliza en la copia exportada; los datos almacenados no se alteran. Esta transformación se documenta en README y se prueba.

## PDF

- Nombre sugerido `oes_informe.pdf`, MIME `application/pdf`, generado con `fpdf2` en memoria.
- Encabezado con nombre del observatorio, fecha/hora de generación y explicación académica.
- Contexto con categorías, búsqueda y rango utilizados; tres KPIs de la selección.
- Una ficha por registro con titular, institución, categoría, fuente, fecha, resumen, URL clicable y auditoría.
- Paginación automática y fuentes libres locales para evitar depender de tipografías del sistema; conservar licencia. Los caracteres no cubiertos por la fuente deben resolverse sin romper la descarga y sin ocultar que hubo sustituciones.
- Selección vacía produce un PDF válido con filtros, KPIs cero y aviso sin resultados.
- La generación no crea archivos permanentes por sesión ni modifica SQLite.

## Accesibilidad y consistencia

Etiquetas visibles, ayuda en los controles, botones diferenciados, contraste suficiente y diseño adaptativo propio de Streamlit. No se utilizan animaciones, imágenes remotas ni gráficos decorativos. Tablero, CSV y PDF comparten la función de filtrado y no mantienen cachés divergentes.

## Referencias

Guía adjunta, secciones 6 y 8–9. [Streamlit LinkColumn](https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.linkcolumn). [fpdf2 y generación en memoria](https://py-pdf.github.io/fpdf2/Tutorial.html).
