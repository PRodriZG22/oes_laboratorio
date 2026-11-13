# Resultados de validación del OES

Validación realizada el **13 de noviembre de 2026, hora de Lima**. La ejecución final terminó con **37 pruebas correctas, cero fallos y cero errores** (ver duración y salida íntegra en `pruebas_automatizadas.txt`; entorno y versiones en `entorno_validacion.json`).

## Entorno comprobado

Windows, Python 3.14.3, SQLite 3.50.4, Streamlit 1.67.0, pandas 3.1.1 y fpdf2 2.9.0. Se utilizó pypdf 7.1.0 exclusivamente para inspeccionar los PDF en las pruebas. Python 3.12 se recomienda para el despliegue; la instalación efectiva en Community Cloud no se ha realizado desde una cuenta externa.

La instalación inicial por terminal encontró una restricción de resolución DNS. Se completó el entorno con paquetes oficiales de PyPI y verificación SHA-256. Las pruebas y el proceso real de la app se ejecutaron posteriormente con el entorno disponible. No se necesitan estos pasos particulares del entorno para una instalación normal mediante `requirements.txt`.

## Seis pruebas obligatorias

| Prueba | Entrada y ejecución | Resultado observado | Evidencia |
| --- | --- | --- | --- |
| P1 | Dos inicializaciones sobre la misma base temporal; comparación literal de los siete campos | 3 altas en la primera, 0 en la segunda; 3 filas y 3 URLs distintas | `P1_doble_carga.txt`, `tests/test_datos.py`, registro íntegro |
| P2 | Seleccionar exclusivamente Universidad pública | Una fila UNMSM; KPIs 1/1/1; comprobado en servicios, AppTest y navegador | `P2_filtro_UNMSM.jpg`, `P5_UNMSM.csv`, registro |
| P3 | Restablecer filtros y buscar PUCP | Una fila PUCP; búsqueda literal e insensible a mayúsculas | `P3_busqueda_PUCP.jpg`, pruebas de servicios e interfaz |
| P4 | Buscar termino_inexistente_oes_987654 | Cero filas, KPIs 0/0/0 y aviso; sin excepción | `P4_sin_resultados.jpg`, pruebas de servicios e interfaz |
| P5 | Descargar CSV con selección Universidad pública | Descarga real desde navegador: BOM EF BB BF, encabezados y una fila UNMSM; acentos y URL intactos | `P5_descarga_navegador.csv`, `P5_UNMSM.csv`, `P5_sin_resultados.csv` |
| P6 | Enviar ficha real con y sin casilla; repetir URL; alta verificada en `oes.db` | Sin confirmación continúa en 3; con confirmación aumenta a 4; duplicado permanece en 4; auditoría y URL correctas | `P6_ficha_y_auditoria.json`, `P6_noticia_verificada.jpg`, prueba de formulario y persistencia |

La base entregada **`oes.db` contiene 4 registros**: los tres ejemplos didácticos de la guía (`estado_de_verificacion = 'didactico'`) y 1 noticia real verificada del Diario Oficial El Peruano (`estado_de_verificacion = 'verificado'`, `verificado_por = 'Piero Rodrigo Zavala Gamero'`). Las pruebas automatizadas siguen utilizando bases temporales separadas.

## Procedencia de la noticia de P6

La ficha corresponde a una nota concreta del [Diario Oficial El Peruano](https://elperuano.pe/noticia/307395-examen-de-beca-18-del-pronabec-se-realizara-el-22-de-noviembre), publicada el **22 de octubre de 2026 a las 10:41**, consultada el 13 de noviembre de 2026. Se contrastaron el titular, la fecha y el anuncio de una evaluación presencial de la convocatoria 2027 de Beca 18 prevista para el 22 de noviembre de 2026. El resumen de la fixture es propio.

La confirmación humana se **simula en AppTest** para verificar el control del formulario. La revisión documental asistida no autentica a una persona y no reemplaza una comprobación humana al registrar información en uso real. Las pruebas son reproducibles sin internet; no vuelven a consultar una fuente que pudiera cambiar.

## Controles complementarios ejecutados

- Creación desde base ausente, archivo de cero bytes y tabla vacía.
- Conservación de una base no vacía sin incorporación automática de ejemplos.
- Auditoría inicial, unicidad de URL y verificado sin responsable rechazado por SQLite.
- Rechazo de confirmación ausente, campos vacíos, límites excedidos, categorías ajenas, fechas imposibles o futuras y URLs inválidas o de portada.
- Rechazo de duplicados sin alterar la ficha anterior.
- Migración de la tabla básica de la guía sin borrar filas ni inventar verificación.
- Base corrupta o esquema desconocido informados sin eliminar datos.
- Cierre de conexiones y uso de ruta de prueba aislada.
- Fechas inclusivas, filtros combinados, categorías vacías y texto con caracteres de regex tratado literalmente.
- CSV vacío con encabezados y neutralización de posibles fórmulas sin modificar SQLite.
- PDF con selección, enlaces, auditoría, sin resultados, paginación extensa y caracteres fuera de cobertura.
- Restablecimiento conjunto de categoría, texto y fechas. Esta comprobación se añadió tras revisar el navegador y corregir el manejo del estado de los filtros.

Los avisos `missing ScriptRunContext` proceden del modo de prueba de Streamlit (`AppTest`). El manejo de filtros en `app.py` fue ajustado para inicializar `st.session_state` antes de instanciar los widgets, eliminando los avisos previos de `Session State API` + valor por defecto.

## Arranque y revisión visual

Un proceso real de Streamlit atendió `http://127.0.0.1:8501`; su endpoint `/_stcore/health` respondió **HTTP 200, `ok`**. El navegador mostró los indicadores, filtros, gráfico y enlaces esperados tanto con los 3 ejemplos iniciales como tras el alta verificada de P6 (`Noticias: 4`).

Se revisaron `dashboard_inicial.jpg`, `tabla_y_exportaciones.jpg`, las capturas P2–P4, `P6_noticia_verificada.jpg` y el diagrama exportado `arquitectura_oes.png`. Se ajustaron las etiquetas del gráfico para mostrarlas completas y el espacio superior del encabezado. El PDF `oes_informe_ejemplo.pdf` se renderizó y se inspeccionó completo: una página, texto legible, fuentes embebidas, enlaces, auditoría y paginación sin solapamientos. La paginación con textos largos también fue probada.

## Alcance de la aprobación técnica

Estas evidencias acreditan los comportamientos del prototipo con el conjunto controlado y las versiones indicadas. No acreditan una nota académica de 20 puntos, representatividad del corpus, autenticidad de identidades declaradas, verdad de futuras noticias ni persistencia de datos en Cloud. La publicación efectiva en GitHub y Community Cloud queda documentada en el README y el plan de despliegue; no se presenta como realizada.
