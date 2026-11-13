from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from oes_servicios import (
    COLUMNAS, calcular_indicadores, filtrar_noticias, generar_csv, generar_pdf, leer_noticias,
)
from preparar_datos import inicializar_base


class ServiciosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "oes.db"
        inicializar_base(self.db)
        self.datos = leer_noticias(self.db)
        self.categorias = self.datos["categoria"].unique().tolist()

    def test_kpis_iniciales_3_3_3(self):
        self.assertEqual(calcular_indicadores(self.datos), (3, 3, 3))

    def test_P2_filtro_universidad_publica_devuelve_UNMSM(self):
        filtrado = filtrar_noticias(self.datos, ["Universidad pública"])
        self.assertEqual(filtrado["institucion"].tolist(), ["UNMSM"])
        self.assertEqual(calcular_indicadores(filtrado), (1, 1, 1))

    def test_P3_busqueda_PUCP_devuelve_una_fila(self):
        for texto in ("PUCP", "pucp", "  PuCp  "):
            with self.subTest(texto=texto):
                filtrado = filtrar_noticias(self.datos, self.categorias, texto)
                self.assertEqual(filtrado["institucion"].tolist(), ["PUCP"])

    def test_P4_termino_inexistente_devuelve_cero(self):
        filtrado = filtrar_noticias(self.datos, self.categorias, "termino_inexistente_oes_987654")
        self.assertTrue(filtrado.empty)
        self.assertEqual(calcular_indicadores(filtrado), (0, 0, 0))

    def test_P5_CSV_BOM_encabezados_y_filas_filtradas(self):
        filtrado = filtrar_noticias(self.datos, ["Universidad pública"])
        contenido = generar_csv(filtrado)
        self.assertTrue(contenido.startswith(b"\xef\xbb\xbf"))
        leido = pd.read_csv(BytesIO(contenido), encoding="utf-8-sig")
        self.assertEqual(leido.columns.tolist(), COLUMNAS)
        self.assertEqual(leido["institucion"].tolist(), ["UNMSM"])
        self.assertEqual(leido["categoria"].iloc[0], "Universidad pública")
        self.assertEqual(leido["url"].iloc[0], "https://www.unmsm.edu.pe/")

    def test_CSV_vacio_conserva_encabezados(self):
        contenido = generar_csv(self.datos.iloc[0:0])
        leido = pd.read_csv(BytesIO(contenido), encoding="utf-8-sig")
        self.assertTrue(leido.empty)
        self.assertEqual(leido.columns.tolist(), COLUMNAS)

    def test_CSV_neutraliza_formulas_sin_modificar_original(self):
        datos = self.datos.copy()
        datos.loc[datos.index[0], "titulo"] = "=1+1"
        leido = pd.read_csv(BytesIO(generar_csv(datos)), encoding="utf-8-sig")
        self.assertEqual(leido["titulo"].iloc[0], "'=1+1")
        self.assertEqual(datos["titulo"].iloc[0], "=1+1")

    def test_fechas_inclusivas_y_combinacion_AND(self):
        dia = date(2026, 11, 6)
        filtrado = filtrar_noticias(self.datos, self.categorias, inicio=dia, fin=dia)
        self.assertEqual(set(filtrado["institucion"]), {"PRONABEC", "UNMSM"})
        self.assertTrue(filtrar_noticias(self.datos, ["Universidad pública"], "PUCP").empty)
        self.assertTrue(filtrar_noticias(self.datos, self.categorias, inicio=dia, fin=date(2026, 11, 5)).empty)

    def test_sin_categorias_y_busqueda_literal(self):
        self.assertTrue(filtrar_noticias(self.datos, []).empty)
        for patron in (".*", "[", "a|b"):
            with self.subTest(patron=patron):
                self.assertTrue(filtrar_noticias(self.datos, self.categorias, patron).empty)

    def test_PDF_seleccion_tiene_trazabilidad_y_URL_clicable(self):
        from pypdf import PdfReader

        datos = filtrar_noticias(self.datos, ["Universidad pública"])
        contenido = generar_pdf(datos, "Universidad pública; 2026-11-06")
        self.assertTrue(contenido.startswith(b"%PDF-"))
        lector = PdfReader(BytesIO(contenido))
        texto = "\n".join(p.extract_text() for p in lector.pages)
        for esperado in ("UNMSM", "Captura UTC", "Didáctico", "Noticias: 1", "Universidad pública"):
            self.assertIn(esperado, texto)
        self.assertNotIn("Ejemplo: programa académico", texto)
        urls = [
            a.get_object().get("/A", {}).get("/URI")
            for p in lector.pages for a in p.get("/Annots", [])
        ]
        self.assertIn("https://www.unmsm.edu.pe/", urls)

    def test_PDF_vacio_y_unicode_no_cubierto(self):
        from pypdf import PdfReader

        vacio = PdfReader(BytesIO(generar_pdf(self.datos.iloc[0:0])))
        self.assertIn("No hay resultados", vacio.pages[0].extract_text())
        datos = self.datos.iloc[:1].copy()
        datos.loc[datos.index[0], "resumen"] = "Texto de prueba \U0001f9ea"
        documento = PdfReader(BytesIO(generar_pdf(datos)))
        self.assertIn("Nota de representación", documento.pages[0].extract_text())

    def test_PDF_paginacion_con_texto_extenso(self):
        from pypdf import PdfReader

        datos = self.datos.copy()
        datos["resumen"] = "Texto de validación extenso con acentos. " * 90
        documento = PdfReader(BytesIO(generar_pdf(datos)))
        self.assertGreater(len(documento.pages), 1)
        self.assertIn("Página", documento.pages[-1].extract_text())


if __name__ == "__main__":
    unittest.main()
