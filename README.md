# Observatorio de Educación Superior

Prototipo académico original basado en `Practica_OES_OBSERVATORIO.docx`, Práctica guiada N.° 08. Permite registrar y consultar fichas de educación superior peruana, conservar trazabilidad y exportar la selección a CSV o PDF.

**La base inicial contiene exactamente tres ejemplos didácticos: PRONABEC, UNMSM y PUCP. Sus URLs apuntan a portales institucionales; no son noticias verificadas.**

## Ejecutar en Windows

Requisitos: Python **3.11 o posterior** y acceso a internet para instalar las dependencias. Una vez instaladas, la aplicación funciona sin servicios de pago ni claves de API.

Abre PowerShell en esta carpeta y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre la dirección que indique Streamlit, normalmente [http://localhost:8501](http://localhost:8501). No necesitas activar el entorno ni cambiar la política de PowerShell. Para detenerlo, presiona `Ctrl+C` en la terminal.

La app crea `oes.db` y los tres ejemplos si la base no existe o está vacía. También puedes preparar los datos de forma explícita:

```powershell
.\.venv\Scripts\python.exe preparar_datos.py
```

La carga utiliza `INSERT OR IGNORE`; ejecutarla nuevamente no duplica las URLs ni modifica los registros ya existentes. Si ya hay noticias reales en una base no vacía, el arranque automático no agrega ejemplos. El comando explícito de preparación sí intenta incorporar los tres ejemplos.

En Linux o macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## Funciones

- Filtros combinados por categoría, texto literal en título o institución y rango inclusivo de fechas.
- Tres indicadores dinámicos: noticias, instituciones y categorías.
- Barras por categoría, tabla con URLs clicables y lectura completa con auditoría.
- Formulario lateral para registrar una nota real con fuente, resumen propio y responsable declarado.
- Confirmación humana obligatoria, validación HTTP(S), rechazo de portadas y control de URL repetida.
- CSV con `utf-8-sig` para Excel y PDF paginado con filtros, enlaces y auditoría.
- Avisos y métricas cero cuando no hay coincidencias; exportaciones vacías válidas.

Al registrar una noticia, los filtros se restablecen para que la nueva fila y el contador queden visibles. La casilla de revisión vuelve a desmarcarse: cada alta requiere una confirmación nueva.

La verificación sintáctica de URL **no comprueba** que la noticia sea verdadera ni que el sitio sea oficial. Quien registra debe abrir el original y comprobar fecha, titular y resumen. `verificado_por` es una identidad declarada, sin autenticación. Las fichas de prueba nunca se convierten automáticamente en verificadas.

## Archivos

| Ruta | Contenido |
| --- | --- |
| `docs/00_PLAN_MAESTRO.md` | Checklist de la rúbrica de 20 puntos y avance secuencial |
| `docs/01_ARQUITECTURA_Y_REQUISITOS.md` | Arquitectura Mermaid, alcance, RF y RNF |
| `docs/02_MODELO_DE_DATOS_Y_ETL.md` | Esquema, semilla exacta, auditoría y reglas de carga |
| `docs/03_DISENO_DASHBOARD_STREAMLIT.md` | Interacción, filtros, KPIs, formulario y salidas |
| `docs/04_PLAN_DE_PRUEBAS_Y_DESPLIEGUE.md` | P1–P6, controles y despliegue paso a paso |
| `docs/05_ANALISIS_CRITICO_Y_ETICA.md` | Cinco respuestas de reflexión y límites metodológicos |
| `preparar_datos.py` | SQLite, inicialización idempotente y registro validado |
| `app.py` | Interfaz Streamlit |
| `oes_servicios.py` | Lectura, filtros, indicadores y exportaciones compartidas |
| `oes.db` | Base de entrega con los tres ejemplos didácticos y 1 noticia real verificada |
| `requirements.txt` | Dependencias de producción fijadas por versión |
| `requirements-dev.txt` | Dependencias de pruebas; agrega pypdf para inspección de PDF |
| `.streamlit/config.toml` | Tema visual y configuración portable |
| `assets/fonts/` | DejaVu Sans y licencia, para PDF sin descargar fuentes |
| `tests/` | Pruebas de datos, servicios e interfaz |
| `evidencias/` | Resultados observados y materiales de validación |

Los seis Markdown se escribieron completos antes de crear código Python. El orden de implementación fue arquitectura, datos/ETL, interfaz/salidas y pruebas/despliegue. Las tareas se controlan en el plan maestro.

## Ejecutar las pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas utilizan bases temporales independientes y `AppTest`, incluido en Streamlit. No borran ni agregan noticias en `oes.db` del proyecto.

Resultado de la validación incluida: **37 pruebas correctas**, sin avisos de `Session State`, endpoint de salud HTTP 200 y comprobación en navegador. Consulta `evidencias/RESULTADOS_PRUEBAS.md` para resultados, capturas (`P2`–`P4`, `P6_noticia_verificada.jpg`), `P1_doble_carga.txt`, `arquitectura_oes.png`, CSV descargado y PDF de ejemplo.

| Prueba | Resultado exigido por la guía |
| --- | --- |
| P1 | Dos cargas dejan 3 filas y 3 URLs distintas |
| P2 | Categoría Universidad pública devuelve solo UNMSM |
| P3 | Buscar PUCP devuelve una fila |
| P4 | Término inexistente produce cero filas y aviso, sin error |
| P5 | CSV conserva encabezados, acentos y las filas filtradas |
| P6 | Alta de nota real con confirmación aumenta el contador y conserva URL directa |

La fixture de P6 reproduce una nota concreta del Diario Oficial El Peruano consultada el 13 de noviembre de 2026. Su fuente y alcance están en `tests/fuente_p6.py` y en las evidencias. La automatización simula la confirmación humana para probar la interfaz; no autentica a una persona ni comprueba en cada ejecución que la fuente siga igual. La semilla automática solo crea los tres ejemplos cuando la base está vacía; la base entregada `oes.db` incorpora además esta noticia real verificada (`verificado_por = "Piero Rodrigo Zavala Gamero"`), sumando 4 registros.

## Desplegar en Streamlit Community Cloud

1. Sube este proyecto a un repositorio GitHub. Incluye los scripts, `requirements.txt`, `.streamlit/` y `assets/`. Puedes incluir `oes.db` u omitirla; `.gitignore` permite subirla.
2. Entra a [share.streamlit.io](https://share.streamlit.io/) y conecta la cuenta con acceso al repositorio.
3. Pulsa **Create app**, selecciona repositorio, rama `main` y archivo de entrada **`app.py`**.
4. En **Advanced settings**, elige Python **3.12**, si está disponible, o una versión compatible 3.11 o posterior. No se necesitan secretos.
5. Pulsa **Deploy**, revisa los logs y comprueba filtros, formulario y descargas.

Los comandos y verificaciones ampliados están en `docs/04_PLAN_DE_PRUEBAS_Y_DESPLIEGUE.md`. Esta entrega está preparada para desplegar; no implica que exista una publicación en una cuenta externa.

**Persistencia:** en Community Cloud las escrituras en SQLite local pueden perderse al reiniciar o desplegar de nuevo. La reconstrucción automática recupera los ejemplos, no las noticias agregadas. Descarga una copia del conjunto completo y conserva respaldos fuera de la instancia. Para operación institucional, usa almacenamiento persistente y controles de acceso.

## Base de datos y respaldo

La tabla `noticias` conserva los siete campos editoriales originales, `id` y la auditoría `fecha_de_captura`, `verificado_por`, `estado_de_verificacion`. La URL es única. La captura se guarda en UTC y la fecha de publicación como día ISO; el día actual del formulario se calcula para Lima.

Puedes indicar otra base para una ejecución aislada:

```powershell
$env:OES_DB_PATH = 'C:\ruta\de\trabajo\oes_prueba.db'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Sustituye la ruta por una carpeta de trabajo real. Para volver a la base predeterminada, elimina la variable en esa terminal con `Remove-Item Env:OES_DB_PATH`. También existe `python preparar_datos.py --db RUTA` para la CLI.

Para un respaldo binario local, detén la app y copia `oes.db`. Un CSV filtrado es una exportación de fichas, no una copia completa de la base ni un mecanismo automático de restauración. Una tabla antigua de la guía puede migrarse sin borrar filas; los registros reales preexistentes se mantienen pendientes de revisión. Un esquema incompatible o una base corrupta se informa sin sobrescribirla.

## Decisiones de exportación y límites

El CSV conserva todas las columnas y la auditoría. Para evitar fórmulas al abrirlo en Excel, los textos que comiencen, incluso tras espacios, con `=`, `+`, `-` o `@` reciben una comilla inicial en la copia exportada; SQLite no cambia.

El PDF incluye una fuente libre local con soporte de español. Los caracteres fuera de su cobertura se representan con `?` y se informa la sustitución; el CSV conserva esos caracteres. No se requieren LibreOffice, navegador ni conexión para exportar.

No se implementan scraping, IA, rankings, transparencia presupuestal, autenticación ni historial de modificaciones. No se infiere calidad universitaria a partir de noticias. Un formulario público sin autenticación debe tratarse como demostración académica, no como recepción institucional de información confiable.

## Fuentes

Guía adjunta: `Practica_OES_OBSERVATORIO.docx`, secciones 1–12, consultada el 13 de noviembre de 2026. Arquitectura e implementación originales; no representan el código ni la infraestructura del OES comercial.

- [Documentación de Streamlit](https://docs.streamlit.io/)
- [Despliegue en Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)
- [fpdf2](https://py-pdf.github.io/fpdf2/)
- [DejaVu Fonts](https://dejavu-fonts.github.io/)
