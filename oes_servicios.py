"""Consulta, filtros y exportaciones del OES, separados de la interfaz."""

from __future__ import annotations

from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd

from preparar_datos import ESTADOS, conectar_base


COLUMNAS = [
    "id", "titulo", "institucion", "categoria", "fuente", "fecha", "url",
    "resumen", "fecha_de_captura", "verificado_por", "estado_de_verificacion",
]
FUENTES = Path(__file__).parent / "assets" / "fonts"


def leer_noticias(ruta: str | Path | None = None) -> pd.DataFrame:
    with conectar_base(ruta) as con:
        return pd.read_sql_query(
            "SELECT " + ", ".join(COLUMNAS) + " FROM noticias ORDER BY fecha DESC, id DESC",
            con,
        )


def filtrar_noticias(
    datos: pd.DataFrame, categorias: list[str] | tuple[str, ...], busqueda: str = "",
    inicio: date | None = None, fin: date | None = None,
) -> pd.DataFrame:
    """AND entre filtros; texto literal; fechas inclusivas; categorías vacías = cero."""
    mascara = datos["categoria"].isin(categorias)
    patron = busqueda.strip()
    if patron:
        mascara &= (
            datos["titulo"].str.contains(patron, case=False, regex=False, na=False)
            | datos["institucion"].str.contains(patron, case=False, regex=False, na=False)
        )
    if inicio is not None and fin is not None and inicio > fin:
        return datos.iloc[0:0].copy()
    fechas = pd.to_datetime(datos["fecha"], format="%Y-%m-%d", errors="coerce")
    if inicio is not None:
        mascara &= fechas >= pd.Timestamp(inicio)
    if fin is not None:
        mascara &= fechas <= pd.Timestamp(fin)
    return datos.loc[mascara].copy()


def calcular_indicadores(datos: pd.DataFrame) -> tuple[int, int, int]:
    return len(datos), int(datos["institucion"].nunique()), int(datos["categoria"].nunique())


def _celda_csv(valor):
    # Evita fórmulas al abrir textos ingresados por usuarios en una hoja de cálculo.
    if isinstance(valor, str) and valor.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + valor
    return valor


def generar_csv(datos: pd.DataFrame) -> bytes:
    seguro = datos.reindex(columns=COLUMNAS).copy()
    for columna in seguro.columns:
        seguro[columna] = seguro[columna].map(_celda_csv)
    return seguro.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")


@lru_cache(maxsize=1)
def _glifos_pdf() -> frozenset[int]:
    # fonttools es una dependencia de fpdf2, no una dependencia del sistema operativo.
    from fontTools.ttLib import TTFont

    conjuntos = []
    for nombre in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        ruta = FUENTES / nombre
        if not ruta.is_file():
            raise FileNotFoundError(f"Falta el recurso de PDF: assets/fonts/{nombre}")
        with TTFont(ruta) as fuente:
            conjuntos.append(set(fuente.getBestCmap()))
    return frozenset(conjuntos[0] & conjuntos[1])


def generar_pdf(datos: pd.DataFrame, contexto: str = "Todos los registros") -> bytes:
    """Informe en memoria; fuente incluida, paginación, enlaces y selección exacta."""
    from fpdf import FPDF

    glifos = _glifos_pdf()

    def texto(valor) -> str:
        if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
            return "Sin responsable (ejemplo o pendiente)"
        limpio = str(valor).replace("\r", "").replace("\t", "    ")
        return "".join(c if c == "\n" or ord(c) in glifos else "?" for c in limpio)

    class Informe(FPDF):
        def header(self):
            self.set_font("DejaVu", "B", 10)
            self.set_text_color(19, 46, 70)
            self.cell(0, 8, "OES / OBSERVATORIO ACADÉMICO", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(8, 127, 140)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(5)

        def footer(self):
            self.set_y(-14)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(90, 103, 115)
            self.cell(0, 5, f"Prototipo educativo · Página {self.page_no()}/{{nb}}", align="C")

    pdf = Informe()
    pdf.set_margins(16, 14, 16)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("DejaVu", "", str(FUENTES / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FUENTES / "DejaVuSans-Bold.ttf"))
    pdf.alias_nb_pages()
    pdf.set_title("Observatorio de Educación Superior - Informe de selección")
    pdf.set_author("OES académico")
    pdf.add_page()

    def parrafo(contenido, *, negrita=False, tamano=9, enlace=""):
        pdf.set_font("DejaVu", "B" if negrita else "", tamano)
        pdf.set_text_color(19, 46, 70)
        pdf.multi_cell(
            0, max(5, tamano * 0.45), texto(contenido), new_x="LMARGIN", new_y="NEXT",
            link=enlace, wrapmode="CHAR" if enlace else "WORD",
        )

    parrafo("Observatorio de Educación Superior", negrita=True, tamano=18)
    parrafo("Informe de registros seleccionados", tamano=11)
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parrafo(f"Generado: {generado}", tamano=8)
    pdf.ln(3)
    parrafo(
        "Uso académico. Los registros didácticos enlazan a portales institucionales y "
        "no son noticias verificadas. La revisión registrada es una declaración."
    )
    parrafo("Filtros: " + contexto, tamano=8)
    noticias, instituciones, categorias = calcular_indicadores(datos)
    pdf.ln(3)
    parrafo(
        f"Noticias: {noticias}    Instituciones: {instituciones}    Categorías: {categorias}",
        negrita=True, tamano=11,
    )
    # Nunca fallar por un emoji o escritura que no esté cubierta por la fuente incluida.
    contenidos = [contexto] + [str(v) for fila in datos.itertuples(index=False) for v in fila]
    if any(any(ord(c) not in glifos and c not in "\n\r\t" for c in s) for s in contenidos):
        parrafo(
            "Nota de representación: los caracteres no cubiertos por la fuente aparecen "
            "como ?. El CSV conserva el texto original.", tamano=8,
        )
    if datos.empty:
        pdf.ln(5)
        parrafo("No hay resultados con esos filtros.")
    for numero, (_, fila) in enumerate(datos.iterrows(), start=1):
        if pdf.get_y() > 235:
            pdf.add_page()
        pdf.ln(6)
        parrafo(f"{numero}. {fila['titulo']}", negrita=True, tamano=11)
        parrafo(f"{fila['institucion']} · {fila['categoria']} · {fila['fecha']}")
        parrafo("Fuente: " + str(fila["fuente"]), tamano=8)
        parrafo("Estado: " + ESTADOS.get(fila["estado_de_verificacion"], "Pendiente de revisión"), tamano=8)
        parrafo(fila["resumen"])
        parrafo(fila["url"], enlace=str(fila["url"]), tamano=8)
        parrafo("Captura UTC: " + str(fila["fecha_de_captura"]), tamano=8)
        parrafo("Verificado por: " + texto(fila["verificado_por"]), tamano=8)
    return bytes(pdf.output())
