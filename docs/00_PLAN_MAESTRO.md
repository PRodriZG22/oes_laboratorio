# Plan maestro del Observatorio de Educación Superior

## Propósito y documento rector

Implementar un prototipo académico original que registre, clasifique, consulte y visualice novedades de educación superior peruana con trazabilidad. El documento rector es `Practica_OES_OBSERVATORIO.docx`, Práctica guiada N.° 08, secciones 1–12, siete páginas. Su rúbrica suma **20 puntos**; no se promete una calificación, sino evidencias comprobables para cada criterio.

La entrega utiliza Python 3.11 o posterior, SQLite y Streamlit. Funciona localmente y se prepara para Streamlit Community Cloud. La base inicial contiene exclusivamente los tres ejemplos de PRONABEC, UNMSM y PUCP de la sección 5. Son datos didácticos con enlaces a portales, **no noticias reales verificadas**.

## Orden obligatorio y puertas de control

No se crea ningún archivo Python hasta que existan los seis Markdown completos. Después se sigue `01` → `02` → `03` → `04`. El documento `05` acompaña todo el trabajo y fundamenta las conclusiones.

### Fase 0 Documentación previa

- [x] Leer íntegramente la guía y extraer rúbrica, registros, P1–P6 y cinco preguntas.
- [x] Crear `docs/00_PLAN_MAESTRO.md`.
- [x] Crear `docs/01_ARQUITECTURA_Y_REQUISITOS.md`.
- [x] Crear `docs/02_MODELO_DE_DATOS_Y_ETL.md`.
- [x] Crear `docs/03_DISENO_DASHBOARD_STREAMLIT.md`.
- [x] Crear `docs/04_PLAN_DE_PRUEBAS_Y_DESPLIEGUE.md`.
- [x] Crear `docs/05_ANALISIS_CRITICO_Y_ETICA.md`.

### Fase 1 Arquitectura y requisitos

- [x] Delimitar alcance académico, flujo y responsabilidades.
- [x] Especificar RF01–RF04 y RNF01–RNF02 con criterios medibles.
- [x] Definir ampliaciones intermedias y límites de almacenamiento en Cloud.
- [x] Preparar entorno reproducible y dependencias de ejecución.

Puerta: contratos claros de datos, interacción, errores y despliegue antes de implementar persistencia.

### Fase 2 Modelo de datos y carga

- [x] Implementar `preparar_datos.py` con funciones reutilizables y CLI.
- [x] Crear `noticias`, URL única, auditoría, controles e índices.
- [x] Cargar exactamente los tres ejemplos con `INSERT OR IGNORE`.
- [x] Separar registros didácticos de registros declarados verificados.
- [x] Validar URL, campos, fecha, responsable y confirmación antes de insertar noticias reales.
- [x] Generar `oes.db` y verificar carga idempotente sin modificar ejemplos.

Puerta: la carga repetida deja tres filas y tres URLs distintas en una base nueva.

### Fase 3 Interfaz y salidas

- [x] Implementar `app.py` con arranque automático de base ausente o vacía.
- [x] Añadir categoría, búsqueda literal y rango inclusivo de fechas.
- [x] Implementar tres KPIs, barras, tabla con enlaces y estado de verificación visible.
- [x] Añadir formulario lateral, comprobación humana y control de duplicados.
- [x] Exportar selección exacta a CSV `utf-8-sig` y PDF con trazabilidad.
- [x] Asegurar estados sin resultados, errores comprensibles y actualización tras registrar.
- [x] Incluir configuración visual y recursos de PDF portables si se requieren.

Puerta: toda salida utiliza el mismo subconjunto filtrado y conserva la advertencia didáctica.

### Fase 4 Pruebas y entrega

- [x] Implementar pruebas reproducibles P1–P6 con bases temporales independientes.
- [x] Ejecutar controles adicionales de integridad, fechas, URL, auditoría y PDF.
- [x] Verificar arranque real de Streamlit y revisar tablero visualmente.
- [x] Guardar resultados y captura en `evidencias/` sin adulterar el resultado de las pruebas.
- [x] Completar `requirements.txt`, `.gitignore` y `README.md`.
- [x] Documentar pasos concretos para GitHub y Streamlit Community Cloud.
- [x] Verificar la base de entrega (tres ejemplos didácticos + 1 noticia real verificada en Paso 7 / P6).
- [x] Empaquetar la entrega sin entornos, cachés, secretos ni archivos transitorios.

La publicación efectiva en cuentas externas queda como paso operativo de quien despliega; estar listo para desplegar no equivale a estar publicado.

## Checklist de la rúbrica

| Criterio de la sección 10 | Puntos | Entregables y evidencia esperada | Estado |
| --- | ---: | --- | --- |
| Arquitectura y explicación de flujo | 4 | Mermaid, alcance y matriz en `01`; explicación de responsabilidades | Completado y contrastado con la implementación |
| Base de datos y trazabilidad | 4 | `oes.db`, `preparar_datos.py`, `02`; URL única y campos de auditoría | Implementado y verificado |
| Aplicación funcional y filtros | 5 | `app.py`, `03`; categoría, texto, fechas, métricas y exportaciones | Implementado; comprobado con AppTest y navegador |
| Pruebas y evidencias | 4 | `04`, pruebas ejecutables, resultados y captura del tablero | 37 pruebas correctas y evidencias guardadas |
| Análisis crítico, ética y conclusiones | 3 | Cinco respuestas académicas y límites en `05` | Completado; limitaciones explícitas |
| **Total** | **20** | Cobertura documental y funcional verificable | No constituye nota asignada |

## Inventario previsto

Obligatorios en raíz: `preparar_datos.py`, `app.py`, `requirements.txt`, `.gitignore`, `README.md` y `oes.db`. Complementos: seis Markdown en `docs/`, pruebas en `tests/`, evidencias en `evidencias/`, configuración en `.streamlit/` y, cuando corresponda, fuente tipográfica libre y su licencia en `assets/`.

## Decisiones que preservan la guía

1. Los siete campos originales de los tres ejemplos se copian literalmente; la auditoría es adicional.
2. El formulario agrega registros reales; no convierte automáticamente ejemplos en noticias verificadas.
3. La semilla automática de carga inicial conserva solo los tres ejemplos; adicionalmente, la base entregada `oes.db` incorpora la noticia real verificada de P6 (Beca 18 / Diario Oficial El Peruano, revisada por `Piero Rodrigo Zavala Gamero`), manteniendo las pruebas automatizadas aisladas en bases temporales.
4. La ausencia de resultados es un estado válido. No se seleccionan categorías significa cero filas.
5. El almacenamiento local de Cloud es efímero: se reconstruyen ejemplos, no se promete recuperar altas manuales perdidas.
6. No se copian identidad visual ni infraestructura del OES comercial. No se atribuyen sus cifras publicitadas a mediciones de este laboratorio.

## Registro de avance

2026-11-13: lectura completa de la guía y elaboración de las seis especificaciones, antes de cualquier archivo Python. Los pasos posteriores se registrarán al ejecutarse y se marcarán solamente con evidencia disponible.

2026-11-13: fase 2 implementada después de la documentación; dos ejecuciones reales de carga informaron 3 altas y 0 altas respectivamente. Consulta SQLite: 3 filas y 3 URLs distintas. Instalación de dependencias en revisión por falta de resolución DNS en el entorno.

2026-11-13: fase 3 implementada. `oes_servicios.py` separa filtros y exportaciones para probarlos sin iniciar Streamlit; no modifica el contrato de `app.py`. Se incluyen fuentes DejaVu con licencia para PDF sin conexión. El acceso a paquetes oficiales está disponible por otra capacidad del entorno y se prepara la ejecución de pruebas.

2026-11-13: validación inicial de 37 pruebas correcta (15,300 s), incluidas P1–P6, arranque real HTTP 200, descarga CSV real, revisión visual del PDF y capturas P2–P4.

2026-11-13 (cierre): se eliminó el aviso de `Session State API` + `default=` en `app.py`, se registró la evidencia CLI de P1 (`evidencias/P1_doble_carga.txt`), se incorporó la noticia real verificada de El Peruano sobre Beca 18 en `oes.db` (`verificado_por = "Piero Rodrigo Zavala Gamero"`, total 4 registros: 3 didácticos + 1 verificado), se capturó `evidencias/P6_noticia_verificada.jpg`, se exportó el diagrama Mermaid a `evidencias/arquitectura_oes.png`, se reejecutaron las 37 pruebas sin avisos de estado y se regeneró el paquete de entrega. Evidencias completas en `evidencias/RESULTADOS_PRUEBAS.md`.
