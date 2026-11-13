from datetime import timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from preparar_datos import (
    CAMPOS_ORIGINALES, DATOS_INICIALES, ErrorEsquema, NoticiaDuplicada,
    asegurar_base_para_app, conectar_base, hoy_lima, inicializar_base,
    registrar_noticia, ruta_base, validar_url,
)
from tests.fuente_p6 import NOTICIA_REAL


class DatosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "oes_prueba.db"
        self.env = patch.dict("os.environ", {"OES_DB_PATH": str(self.db)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def total(self):
        with conectar_base() as con:
            return con.execute("SELECT count(*) FROM noticias").fetchone()[0]

    def test_P1_carga_dos_veces_sin_duplicacion_y_campos_exactos(self):
        primera = inicializar_base()
        segunda = inicializar_base()
        self.assertEqual((primera["insertados"], segunda["insertados"]), (3, 0))
        with conectar_base() as con:
            conteos = con.execute("SELECT count(*), count(DISTINCT url) FROM noticias").fetchone()
            filas = con.execute("SELECT " + ",".join(CAMPOS_ORIGINALES) + " FROM noticias ORDER BY id").fetchall()
        self.assertEqual(tuple(conteos), (3, 3))
        self.assertEqual(tuple(tuple(fila) for fila in filas), DATOS_INICIALES)

    def test_auditoria_inicial_no_declara_verificados(self):
        inicializar_base()
        with conectar_base() as con:
            filas = con.execute("SELECT * FROM noticias").fetchall()
        for fila in filas:
            self.assertEqual(fila["estado_de_verificacion"], "didactico")
            self.assertIsNone(fila["verificado_por"])
            self.assertRegex(fila["fecha_de_captura"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_base_ausente_se_inicializa_automaticamente(self):
        self.assertFalse(self.db.exists())
        self.assertEqual(asegurar_base_para_app()["total"], 3)

    def test_archivo_cero_bytes_se_recupera(self):
        self.db.touch()
        self.assertEqual(asegurar_base_para_app()["total"], 3)

    def test_tabla_vacia_se_recupera(self):
        inicializar_base(cargar_ejemplos=False)
        self.assertEqual(self.total(), 0)
        self.assertEqual(asegurar_base_para_app()["total"], 3)

    def test_base_no_vacia_no_recibe_ejemplos_por_arranque(self):
        registrar_noticia(**NOTICIA_REAL)
        asegurar_base_para_app()
        self.assertEqual(self.total(), 1)

    def test_P6_registro_real_con_url_y_auditoria(self):
        inicializar_base()
        identificador = registrar_noticia(**NOTICIA_REAL)
        self.assertEqual(self.total(), 4)
        with conectar_base() as con:
            fila = con.execute("SELECT * FROM noticias WHERE id=?", (identificador,)).fetchone()
        self.assertEqual(fila["url"], NOTICIA_REAL["url"])
        self.assertEqual(fila["estado_de_verificacion"], "verificado")
        self.assertEqual(fila["verificado_por"], NOTICIA_REAL["verificado_por"])
        self.assertTrue(fila["fecha_de_captura"])

    def test_registro_exige_confirmacion_explicita(self):
        inicializar_base()
        for confirmacion in (False, None, 1, "sí"):
            with self.subTest(confirmacion=confirmacion), self.assertRaises(ValueError):
                registrar_noticia(**{**NOTICIA_REAL, "confirmacion": confirmacion})
        self.assertEqual(self.total(), 3)

    def test_duplicado_no_modifica_ficha(self):
        registrar_noticia(**NOTICIA_REAL)
        with self.assertRaises(NoticiaDuplicada):
            registrar_noticia(**{**NOTICIA_REAL, "titulo": "Otro titular"})
        with conectar_base() as con:
            self.assertEqual(con.execute("SELECT titulo FROM noticias").fetchone()[0], NOTICIA_REAL["titulo"])
        self.assertEqual(self.total(), 1)

    def test_url_invalida_o_portada_se_rechaza(self):
        for url in (
            "ftp://www.pucp.edu.pe/noticia", "javascript:alert(1)",
            "https://", "https://usuario:clave@www.pucp.edu.pe/nota",
            "https://www.pucp.edu.pe/", "https://dominio sin espacio/nota",
            "https://www.pucp.edu.pe:abc/nota", "https://-invalido.pe/nota",
            "https://www.pucp.edu.pe:0/nota", "https://www.pucp.edu.pe/nota\nextra",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validar_url(url)
        self.assertEqual(validar_url(NOTICIA_REAL["url"]), NOTICIA_REAL["url"])

    def test_campos_vacios_y_longitudes_se_rechazan(self):
        for campo in ("titulo", "institucion", "fuente", "resumen", "verificado_por"):
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                registrar_noticia(**{**NOTICIA_REAL, campo: "   "})
        with self.assertRaises(ValueError):
            registrar_noticia(**{**NOTICIA_REAL, "titulo": "a" * 301})
        with self.assertRaises(ValueError):
            registrar_noticia(**{**NOTICIA_REAL, "categoria": "Categoría inexistente"})

    def test_fechas_imposibles_y_futuras_se_rechazan(self):
        for fecha in ("2026-02-30", "sin fecha", (hoy_lima() + timedelta(days=1)).isoformat()):
            with self.subTest(fecha=fecha), self.assertRaises(ValueError):
                registrar_noticia(**{**NOTICIA_REAL, "fecha": fecha})

    def test_restricciones_unicidad_y_responsable_en_sqlite(self):
        inicializar_base()
        with self.assertRaises(sqlite3.IntegrityError), conectar_base() as con:
            con.execute("UPDATE noticias SET url=? WHERE institucion='PUCP'", (DATOS_INICIALES[0][5],))
        with self.assertRaises(sqlite3.IntegrityError), conectar_base() as con:
            con.execute("UPDATE noticias SET estado_de_verificacion='verificado' WHERE institucion='PUCP'")

    def test_migracion_basica_conserva_datos_y_no_inventa_verificacion(self):
        with conectar_base() as con:
            con.execute("""CREATE TABLE noticias (
                id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
                institucion TEXT NOT NULL, categoria TEXT NOT NULL, fuente TEXT NOT NULL,
                fecha TEXT NOT NULL, url TEXT NOT NULL UNIQUE, resumen TEXT NOT NULL)""")
            con.executemany(
                "INSERT INTO noticias (titulo,institucion,categoria,fuente,fecha,url,resumen) VALUES (?,?,?,?,?,?,?)",
                DATOS_INICIALES,
            )
            con.execute(
                "INSERT INTO noticias (titulo,institucion,categoria,fuente,fecha,url,resumen) VALUES (?,?,?,?,?,?,?)",
                tuple(NOTICIA_REAL[c] for c in CAMPOS_ORIGINALES),
            )
        asegurar_base_para_app()
        self.assertEqual(self.total(), 4)
        with conectar_base() as con:
            estados = [fila[0] for fila in con.execute("SELECT estado_de_verificacion FROM noticias ORDER BY id")]
        self.assertEqual(estados, ["didactico", "didactico", "didactico", "pendiente"])

    def test_base_corrupta_no_se_borra(self):
        contenido = b"Base corrupta de prueba, conservar bytes"
        self.db.write_bytes(contenido)
        with self.assertRaises(sqlite3.DatabaseError):
            asegurar_base_para_app()
        self.assertEqual(self.db.read_bytes(), contenido)

    def test_esquema_incompatible_se_rechaza(self):
        with conectar_base() as con:
            con.execute("CREATE TABLE noticias (id INTEGER, dato TEXT)")
        with self.assertRaises(ErrorEsquema):
            asegurar_base_para_app()

    def test_ruta_parametrizada_y_conexion_cerrada(self):
        self.assertEqual(ruta_base(), self.db.resolve())
        inicializar_base()
        with conectar_base() as con:
            con.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):
            con.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
