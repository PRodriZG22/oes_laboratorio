"""Tablero OES: ejecutar con python -m streamlit run app.py."""

from __future__ import annotations

import sqlite3

import pandas as pd
import streamlit as st

from oes_servicios import (
    calcular_indicadores, filtrar_noticias, generar_csv, generar_pdf, leer_noticias,
)
from preparar_datos import (
    CATEGORIAS, ESTADOS, ErrorEsquema, NoticiaDuplicada,
    asegurar_base_para_app, hoy_lima, registrar_noticia,
)


CONFIRMACION = (
    "Confirmo que abrí la URL directa y comprobé el titular, la fecha y el resumen "
    "con la fuente original."
)


def restablecer_filtros() -> None:
    # Asignar valores explícitos también reemplaza el estado enviado por el navegador.
    # Borrar solo las claves puede restaurar accidentalmente una selección anterior.
    st.session_state["filtro_categorias"] = st.session_state.get("opciones_categorias", [])
    st.session_state["filtro_busqueda"] = ""
    if "limites_fechas" in st.session_state:
        st.session_state["filtro_fechas"] = st.session_state["limites_fechas"]
    st.session_state.pop("detalle_id", None)


def formulario_registro() -> None:
    with st.sidebar.expander("Registrar noticia verificada", expanded=False):
        st.caption("Abre primero la nota original. Completa una ficha por noticia.")
        with st.form("registro_noticia", clear_on_submit=False):
            titulo = st.text_input("Título de la noticia", max_chars=300, key="nuevo_titulo")
            institucion = st.text_input("Institución", max_chars=160, key="nueva_institucion")
            categoria = st.selectbox("Categoría de la noticia", CATEGORIAS, key="nueva_categoria")
            fuente = st.text_input("Fuente oficial", max_chars=200, key="nueva_fuente")
            fecha = st.date_input(
                "Fecha de publicación", value=hoy_lima(), max_value=hoy_lima(),
                key="nueva_fecha", format="DD/MM/YYYY",
            )
            url = st.text_input("URL directa de la noticia", max_chars=2048, key="nueva_url")
            resumen = st.text_area("Resumen propio", max_chars=4000, key="nuevo_resumen")
            verificado_por = st.text_input(
                "Verificado por", max_chars=120, key="nuevo_verificador",
                help="Identificador público de quien revisa; no ingreses DNI ni datos sensibles.",
            )
            confirmacion = st.checkbox(CONFIRMACION, value=False, key="confirmacion_humana")
            enviado = st.form_submit_button("Guardar noticia", type="primary", width="stretch")
        st.caption("La revisión es declarada. Al guardar se restablecen los filtros.")
        if enviado:
            try:
                registrar_noticia(
                    titulo=titulo, institucion=institucion, categoria=categoria,
                    fuente=fuente, fecha=fecha, url=url, resumen=resumen,
                    verificado_por=verificado_por, confirmacion=confirmacion,
                )
            except NoticiaDuplicada as exc:
                st.warning(str(exc))
            except ValueError as exc:
                st.error(str(exc))
            except (sqlite3.Error, OSError):
                st.error("No se pudo guardar. Revisa permisos de oes.db o inténtalo de nuevo.")
            else:
                # Se aplica en el siguiente rerun, antes de instanciar los widgets.
                st.session_state["alta_exitosa"] = True
                st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="OES · Observatorio académico", page_icon="📘", layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """<style>
        .block-container {padding-top: 4.5rem; padding-bottom: 2rem; max-width: 1500px;}
        [data-testid="stMetricValue"] {color: #132e46;}
        [data-testid="stMetricLabel"] {color: #4a6175;}
        h1 {letter-spacing: -0.035em;}
        </style>""", unsafe_allow_html=True,
    )
    st.caption("MONITOREO INSTITUCIONAL  /  EDUCACIÓN SUPERIOR PERUANA")
    st.title("Observatorio de Educación Superior")
    st.write("Consulta novedades, revisa su procedencia y exporta la información seleccionada.")
    st.info(
        "Prototipo académico. Los tres ejemplos de la guía enlazan a portales institucionales "
        "y no son noticias verificadas. Los conteos describen registros, no calidad universitaria.",
        icon="ℹ️",
    )
    alta_exitosa = st.session_state.pop("alta_exitosa", False)
    try:
        asegurar_base_para_app()
        datos = leer_noticias()
    except (sqlite3.Error, OSError, ErrorEsquema) as exc:
        st.error(
            "No se pudo abrir la base OES. Cierra otras operaciones y revisa permisos o esquema. "
            "Si persiste, respalda oes.db antes de repararla."
        )
        st.caption(str(exc))
        st.stop()

    fechas_validas = pd.to_datetime(datos["fecha"], format="%Y-%m-%d", errors="coerce")
    if fechas_validas.isna().any():
        st.warning("Hay fichas antiguas con fecha inválida: no se incluyen en el rango de fechas.")
    minimo = fechas_validas.min().date() if fechas_validas.notna().any() else hoy_lima()
    maximo = fechas_validas.max().date() if fechas_validas.notna().any() else hoy_lima()
    categorias = sorted(datos["categoria"].dropna().unique().tolist())
    st.session_state["opciones_categorias"] = categorias
    st.session_state["limites_fechas"] = (minimo, maximo)
    if alta_exitosa:
        restablecer_filtros()
        # Desmarcar antes de crear el formulario: cada alta exige nueva confirmación.
        st.session_state["confirmacion_humana"] = False
        st.success("Noticia registrada. Se restablecieron los filtros para mostrar todos los registros.")
    else:
        if "filtro_categorias" not in st.session_state:
            st.session_state["filtro_categorias"] = categorias
        elif any(c not in categorias for c in st.session_state["filtro_categorias"]):
            st.session_state["filtro_categorias"] = [
                c for c in st.session_state["filtro_categorias"] if c in categorias
            ]
        if "filtro_fechas" not in st.session_state:
            st.session_state["filtro_fechas"] = (minimo, maximo)

    st.sidebar.title("Explorar registros")
    st.sidebar.caption(f"{len(datos)} registros disponibles · Captura manual y trazable")
    st.sidebar.button(
        "Restablecer filtros", key="boton_restablecer", on_click=restablecer_filtros,
        width="stretch",
    )
    seleccion = st.sidebar.multiselect(
        "Categoría", categorias, key="filtro_categorias",
        help="Sin categorías seleccionadas, el resultado es cero.",
    )
    busqueda = st.sidebar.text_input(
        "Buscar título o institución", key="filtro_busqueda", placeholder="Ej. PUCP",
        max_chars=300, help="Busca texto literal, sin distinguir mayúsculas.",
    )
    rango = st.sidebar.date_input(
        "Rango de publicación", key="filtro_fechas",
        min_value=minimo, max_value=max(maximo, hoy_lima()), format="DD/MM/YYYY",
    )
    if isinstance(rango, (tuple, list)) and len(rango) == 2 and rango[0] <= rango[1]:
        inicio, fin = rango
        filtrado = filtrar_noticias(datos, seleccion, busqueda, inicio, fin)
        periodo = f"{inicio.isoformat()} a {fin.isoformat()} (inclusive)"
    else:
        filtrado = datos.iloc[0:0].copy()
        periodo = "Rango incompleto o inválido"
        st.sidebar.warning("Selecciona las dos fechas del rango, con el inicio antes del fin.")
    formulario_registro()
    st.sidebar.divider()
    st.sidebar.caption(
        "En Streamlit Cloud las altas locales pueden perderse al reiniciar. "
        "Exporta y conserva una copia fuera de la aplicación."
    )

    st.subheader("Panorama de la selección")
    n, i, c = calcular_indicadores(filtrado)
    for columna, etiqueta, valor, ayuda in zip(
        st.columns(3), ("Noticias", "Instituciones", "Categorías"), (n, i, c),
        ("Fichas en la selección, incluidos ejemplos", "Instituciones distintas", "Categorías distintas"),
    ):
        with columna.container(border=True):
            st.metric(etiqueta, valor, help=ayuda)
    st.caption(f"{n} de {len(datos)} registros · {periodo}")

    izquierda, derecha = st.columns([1.65, 1])
    with izquierda:
        st.subheader("Distribución por categoría")
        if filtrado.empty:
            st.info("No hay resultados con esos filtros.")
        else:
            distribucion = (
                filtrado["categoria"].value_counts().rename_axis("Categoría")
                .rename("Registros").reset_index()
            )
            st.vega_lite_chart(
                distribucion,
                {
                    "mark": {"type": "bar", "cornerRadiusEnd": 3},
                    "encoding": {
                        "y": {
                            "field": "Categoría", "type": "nominal", "sort": "-x",
                            "axis": {"title": None, "labelLimit": 220},
                        },
                        "x": {
                            "field": "Registros", "type": "quantitative",
                            "axis": {"title": None, "tickMinStep": 1},
                        },
                        "color": {"value": "#087F8C"},
                        "tooltip": [
                            {"field": "Categoría", "type": "nominal"},
                            {"field": "Registros", "type": "quantitative", "format": "d"},
                        ],
                    },
                    "height": 200,
                    "config": {"view": {"stroke": None}},
                },
                width="stretch",
            )
    with derecha:
        st.subheader("Estado de los registros")
        for estado, etiqueta in ESTADOS.items():
            cantidad = int((filtrado["estado_de_verificacion"] == estado).sum())
            st.write(f"**{cantidad}** · {etiqueta}")
        st.caption("Una revisión declarada no autentica a la persona ni certifica la calidad institucional.")

    st.subheader("Noticias registradas")
    tabla = filtrado.copy()
    tabla["estado_de_verificacion"] = tabla["estado_de_verificacion"].map(ESTADOS).fillna("Pendiente de revisión")
    st.dataframe(
        tabla,
        column_order=[
            "fecha", "institucion", "categoria", "titulo", "fuente", "url",
            "estado_de_verificacion", "fecha_de_captura", "verificado_por", "resumen",
        ],
        column_config={
            "id": None,
            "fecha": st.column_config.TextColumn("Publicación", width="small"),
            "institucion": st.column_config.TextColumn("Institución", width="small"),
            "categoria": st.column_config.TextColumn("Categoría", width="medium"),
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "fuente": "Fuente",
            "url": st.column_config.LinkColumn("URL de la fuente", width="medium"),
            "estado_de_verificacion": st.column_config.TextColumn("Verificación", width="medium"),
            "fecha_de_captura": "Captura UTC", "verificado_por": "Verificado por",
            "resumen": "Resumen",
        },
        hide_index=True, width="stretch", height=190 if len(tabla) <= 3 else 330,
    )
    if not filtrado.empty:
        with st.expander("Leer ficha completa y auditoría"):
            opciones = filtrado["id"].tolist()
            if st.session_state.get("detalle_id") not in opciones:
                st.session_state.pop("detalle_id", None)
            elegida = st.selectbox(
                "Selecciona una ficha", opciones, key="detalle_id",
                format_func=lambda valor: str(filtrado.loc[filtrado["id"] == valor, "titulo"].iloc[0]),
            )
            fila = filtrado.loc[filtrado["id"] == elegida].iloc[0]
            st.text(fila["resumen"])
            st.link_button("Abrir fuente original", fila["url"])
            st.caption(
                f"Captura: {fila['fecha_de_captura']} · Responsable: "
                f"{fila['verificado_por'] or 'Sin responsable (ejemplo o pendiente)'}"
            )

    contexto = (
        f"Categorías: {', '.join(seleccion) or 'ninguna'}; "
        f"búsqueda: {busqueda.strip() or '(vacía)'}; publicación: {periodo}"
    )
    st.subheader("Exportar selección")
    csv_col, pdf_col, nota_col = st.columns([1, 1, 2])
    csv_col.download_button(
        "Exportar CSV", data=generar_csv(filtrado), file_name="oes_resultados.csv",
        mime="text/csv", width="stretch", key="descarga_csv",
    )
    try:
        documento = generar_pdf(filtrado, contexto)
    except (OSError, ValueError, RuntimeError) as exc:
        pdf_col.warning("No se pudo generar el PDF. Revisa los recursos de assets/fonts.")
        pdf_col.caption(str(exc))
    else:
        pdf_col.download_button(
            "Exportar PDF", data=documento, file_name="oes_informe.pdf",
            mime="application/pdf", width="stretch", key="descarga_pdf",
        )
    nota_col.caption(
        "Ambos archivos incluyen la selección y su auditoría. CSV con UTF-8 para Excel; "
        "los posibles textos de fórmula se neutralizan solo al exportar."
    )
    with st.expander("Alcance y metodología"):
        st.write(
            "La carga inicial contiene exactamente PRONABEC, UNMSM y PUCP de la guía. "
            "Las altas reales requieren URL directa, resumen propio y confirmación de revisión. "
            "El sistema valida formato y duplicados; no comprueba automáticamente el contenido."
        )
        st.write(
            "No hay autenticación ni historial de cambios. El tablero no mide calidad, "
            "cumplimiento normativo ni ejecución presupuestal. SQLite en Cloud no ofrece "
            "persistencia garantizada: conserva respaldos fuera de la instancia."
        )
    st.caption("OES académico · Python / SQLite / Streamlit · Implementación educativa original")


if __name__ == "__main__":
    main()
