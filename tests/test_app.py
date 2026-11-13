from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from preparar_datos import conectar_base
from tests.fuente_p6 import NOTICIA_REAL


APP = Path(__file__).resolve().parents[1] / "app.py"


class InterfazTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "oes.db"
        self.env = patch.dict("os.environ", {"OES_DB_PATH": str(self.db)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertEqual(len(self.app.exception), 0)

    def kpis(self):
        return tuple(int(m.value) for m in self.app.metric)

    def test_arranque_auto_y_KPIs(self):
        self.assertTrue(self.db.is_file())
        self.assertEqual(self.kpis(), (3, 3, 3))
        self.assertEqual(len(self.app.dataframe[0].value), 3)

    def test_P2_interfaz_categoria_UNMSM(self):
        self.app.multiselect(key="filtro_categorias").set_value(["Universidad pública"]).run()
        self.assertEqual(self.app.dataframe[0].value["institucion"].tolist(), ["UNMSM"])
        self.assertEqual(self.kpis(), (1, 1, 1))
        self.assertFalse(self.app.exception)

    def test_P3_interfaz_busqueda_PUCP(self):
        self.app.text_input(key="filtro_busqueda").set_value("PUCP").run()
        self.assertEqual(self.app.dataframe[0].value["institucion"].tolist(), ["PUCP"])

    def test_P4_interfaz_sin_resultados_sin_error(self):
        self.app.text_input(key="filtro_busqueda").set_value("termino_inexistente_oes_987654").run()
        self.assertEqual(self.kpis(), (0, 0, 0))
        self.assertTrue(self.app.dataframe[0].value.empty)
        self.assertTrue(any("No hay resultados" in aviso.value for aviso in self.app.info))
        self.assertFalse(self.app.exception)

    def test_fecha_inclusiva_y_rango_incompleto(self):
        self.app.date_input(key="filtro_fechas").set_value((date(2026, 11, 6), date(2026, 11, 6))).run()
        self.assertEqual(self.kpis(), (2, 2, 2))
        self.app.date_input(key="filtro_fechas").set_value((date(2026, 11, 6),)).run()
        self.assertEqual(self.kpis(), (0, 0, 0))
        self.assertFalse(self.app.exception)

    def test_sin_categorias_se_maneja(self):
        self.app.multiselect(key="filtro_categorias").set_value([]).run()
        self.assertEqual(self.kpis(), (0, 0, 0))
        self.assertFalse(self.app.exception)

    def test_restablecer_recupera_categorias_texto_y_fechas(self):
        self.app.multiselect(key="filtro_categorias").set_value(["Universidad pública"]).run()
        self.app.text_input(key="filtro_busqueda").set_value("inexistente").run()
        self.app.date_input(key="filtro_fechas").set_value((date(2026, 11, 6), date(2026, 11, 6))).run()
        self.app.button(key="boton_restablecer").click().run()
        self.assertEqual(self.kpis(), (3, 3, 3))
        self.assertEqual(self.app.text_input(key="filtro_busqueda").value, "")
        self.assertEqual(len(self.app.multiselect(key="filtro_categorias").value), 3)
        self.assertEqual(tuple(self.app.date_input(key="filtro_fechas").value),
                         (date(2026, 11, 5), date(2026, 11, 6)))
        self.assertFalse(self.app.exception)

    def test_P6_formulario_confirmacion_alta_auditoria_y_duplicado(self):
        self.app.text_input(key="nuevo_titulo").set_value(NOTICIA_REAL["titulo"])
        self.app.text_input(key="nueva_institucion").set_value(NOTICIA_REAL["institucion"])
        self.app.selectbox(key="nueva_categoria").set_value(NOTICIA_REAL["categoria"])
        self.app.text_input(key="nueva_fuente").set_value(NOTICIA_REAL["fuente"])
        self.app.date_input(key="nueva_fecha").set_value(date.fromisoformat(NOTICIA_REAL["fecha"]))
        self.app.text_input(key="nueva_url").set_value(NOTICIA_REAL["url"])
        self.app.text_area(key="nuevo_resumen").set_value(NOTICIA_REAL["resumen"])
        self.app.text_input(key="nuevo_verificador").set_value(NOTICIA_REAL["verificado_por"])
        self.app.button(key="FormSubmitter:registro_noticia-Guardar noticia").click().run()
        self.assertEqual(self.kpis()[0], 3)
        self.assertTrue(self.app.error)
        self.app.checkbox(key="confirmacion_humana").set_value(True)
        self.app.button(key="FormSubmitter:registro_noticia-Guardar noticia").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.kpis()[0], 4)
        self.assertFalse(self.app.checkbox(key="confirmacion_humana").value)
        with conectar_base() as con:
            fila = con.execute("SELECT * FROM noticias WHERE url=?", (NOTICIA_REAL["url"],)).fetchone()
            self.assertEqual(fila["estado_de_verificacion"], "verificado")
            self.assertTrue(fila["fecha_de_captura"])
        self.app.checkbox(key="confirmacion_humana").set_value(True)
        self.app.button(key="FormSubmitter:registro_noticia-Guardar noticia").click().run()
        self.assertEqual(self.kpis()[0], 4)
        self.assertTrue(any("ya está registrada" in aviso.value for aviso in self.app.warning))


if __name__ == "__main__":
    unittest.main()
