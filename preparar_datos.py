"""Persistencia del OES académico. Importar el módulo no crea ni modifica archivos."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import re
import sqlite3
from typing import Iterator
from urllib.parse import urlsplit


CATEGORIAS = (
    "Ente rector",
    "Universidad pública",
    "Universidad privada",
    "Instituto de educación superior",
    "Otro",
)
ESTADOS = {
    "didactico": "Didáctico · no verificado",
    "pendiente": "Pendiente de revisión",
    "verificado": "Verificado · revisión declarada",
}
CAMPOS_ORIGINALES = (
    "titulo", "institucion", "categoria", "fuente", "fecha", "url", "resumen"
)
# Transcripción literal de los siete campos de la sección 5 de la guía.
DATOS_INICIALES = (
    (
        "Ejemplo: convocatoria de becas", "PRONABEC", "Ente rector",
        "Portal institucional (ejemplo)", "2026-11-06",
        "https://www.pronabec.gob.pe/", "Registro didáctico: verificar nota original.",
    ),
    (
        "Ejemplo: actividad de investigación", "UNMSM", "Universidad pública",
        "Portal institucional (ejemplo)", "2026-11-06",
        "https://www.unmsm.edu.pe/", "Registro didáctico: verificar noticia original.",
    ),
    (
        "Ejemplo: programa académico", "PUCP", "Universidad privada",
        "Portal institucional (ejemplo)", "2026-11-05",
        "https://www.pucp.edu.pe/", "Registro didáctico: verificar noticia original.",
    ),
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS noticias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL CHECK(length(trim(titulo)) > 0),
    institucion TEXT NOT NULL CHECK(length(trim(institucion)) > 0),
    categoria TEXT NOT NULL CHECK(categoria IN (
        'Ente rector', 'Universidad pública', 'Universidad privada',
        'Instituto de educación superior', 'Otro'
    )),
    fuente TEXT NOT NULL CHECK(length(trim(fuente)) > 0),
    fecha TEXT NOT NULL CHECK(
        fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(fecha) IS NOT NULL AND date(fecha) = fecha
    ),
    url TEXT NOT NULL UNIQUE CHECK(url LIKE 'https://%' OR url LIKE 'http://%'),
    resumen TEXT NOT NULL CHECK(length(trim(resumen)) > 0),
    fecha_de_captura TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    verificado_por TEXT,
    estado_de_verificacion TEXT NOT NULL DEFAULT 'pendiente'
        CHECK(estado_de_verificacion IN ('didactico', 'pendiente', 'verificado')),
    CHECK(estado_de_verificacion <> 'verificado' OR
        (verificado_por IS NOT NULL AND length(trim(verificado_por)) > 0))
)
"""


class ErrorEsquema(ValueError):
    """La base existente requiere revisión, sin eliminación automática."""


class NoticiaDuplicada(ValueError):
    """La URL ya fue registrada."""


def hoy_lima() -> date:
    """Lima usa UTC-5; no requiere tzdata del sistema en Windows o Cloud."""
    return datetime.now(timezone(timedelta(hours=-5))).date()


def ruta_base(ruta: str | Path | None = None) -> Path:
    elegida = ruta if ruta is not None else os.environ.get(
        "OES_DB_PATH", str(Path(__file__).with_name("oes.db"))
    )
    return Path(elegida).expanduser().resolve()


@contextmanager
def conectar_base(ruta: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Una conexión por operación; commit/rollback y cierre explícito."""
    con = sqlite3.connect(ruta_base(ruta), timeout=10)
    con.row_factory = sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()


def _preparar_esquema(con: sqlite3.Connection) -> None:
    existe = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='noticias'"
    ).fetchone()
    if not existe:
        con.execute(ESQUEMA)
    else:
        campos = {fila["name"] for fila in con.execute("PRAGMA table_info(noticias)")}
        if not {"id", *CAMPOS_ORIGINALES}.issubset(campos):
            raise ErrorEsquema(
                "El esquema de noticias es incompatible. Respalde oes.db y revise sus columnas."
            )
        # Migración no destructiva de la tabla básica de la guía.
        if "fecha_de_captura" not in campos:
            con.execute(
                "ALTER TABLE noticias ADD COLUMN fecha_de_captura TEXT NOT NULL DEFAULT ''"
            )
        if "verificado_por" not in campos:
            con.execute("ALTER TABLE noticias ADD COLUMN verificado_por TEXT")
        if "estado_de_verificacion" not in campos:
            con.execute(
                "ALTER TABLE noticias ADD COLUMN estado_de_verificacion "
                "TEXT NOT NULL DEFAULT 'pendiente'"
            )
            for ejemplo in DATOS_INICIALES:
                con.execute(
                    "UPDATE noticias SET estado_de_verificacion='didactico' WHERE "
                    + " AND ".join(f"{campo}=?" for campo in CAMPOS_ORIGINALES),
                    ejemplo,
                )
        con.execute(
            "UPDATE noticias SET fecha_de_captura=strftime('%Y-%m-%dT%H:%M:%SZ','now') "
            "WHERE fecha_de_captura IS NULL OR trim(fecha_de_captura)=''"
        )
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_noticias_url ON noticias(url)")
    except sqlite3.IntegrityError as exc:
        raise ErrorEsquema(
            "Hay URLs duplicadas en la base existente. Respalde y concilie las fichas."
        ) from exc
    con.execute("CREATE INDEX IF NOT EXISTS idx_noticias_fecha ON noticias(fecha)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_noticias_categoria ON noticias(categoria)")


def inicializar_base(
    ruta: str | Path | None = None, *, cargar_ejemplos: bool = True
) -> dict:
    """Crea/migra el esquema y, si se solicita, inserta solo los tres ejemplos."""
    destino = ruta_base(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with conectar_base(destino) as con:
        con.execute("BEGIN IMMEDIATE")
        _preparar_esquema(con)
        antes = con.execute("SELECT count(*) FROM noticias").fetchone()[0]
        if cargar_ejemplos:
            con.executemany(
                """INSERT OR IGNORE INTO noticias
                   (titulo,institucion,categoria,fuente,fecha,url,resumen,
                    estado_de_verificacion)
                   VALUES (?,?,?,?,?,?,?,'didactico')""",
                DATOS_INICIALES,
            )
        total = con.execute("SELECT count(*) FROM noticias").fetchone()[0]
    return {"ruta": str(destino), "total": total, "insertados": total - antes}


def asegurar_base_para_app(ruta: str | Path | None = None) -> dict:
    """Recupera base ausente/vacía; conserva sin añadir ejemplos una base poblada."""
    resultado = inicializar_base(ruta, cargar_ejemplos=False)
    if resultado["total"] == 0:
        return inicializar_base(ruta, cargar_ejemplos=True)
    return resultado


def validar_url(url: str, *, exigir_directa: bool = True) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("La URL debe comenzar con http:// o https://.")
    if len(url) > 2048 or any(c.isspace() or ord(c) < 32 for c in url):
        raise ValueError("La URL contiene espacios, controles o supera 2048 caracteres.")
    if any(c in url for c in '<>"\\'):
        raise ValueError("La URL contiene caracteres no válidos.")
    try:
        partes = urlsplit(url)
        host = (partes.hostname or "").encode("idna").decode("ascii")
        puerto = partes.port  # Valida también puertos mal formados.
    except (ValueError, UnicodeError) as exc:
        raise ValueError("La URL no tiene una estructura válida.") from exc
    etiquetas = host.split(".")
    if (
        not host or len(host) > 253 or len(etiquetas) < 2
        or any(not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", e)
               for e in etiquetas)
        or partes.username is not None or partes.password is not None
        or (puerto is not None and not 1 <= puerto <= 65535)
    ):
        raise ValueError("Use una URL con dominio válido y sin credenciales.")
    if exigir_directa and not (partes.path.strip("/") or partes.query):
        raise ValueError("Copie la URL directa de la noticia, no la portada del portal.")
    return url


def registrar_noticia(
    *, titulo: str, institucion: str, categoria: str, fuente: str,
    fecha: date | str, url: str, resumen: str, verificado_por: str,
    confirmacion: bool, ruta: str | Path | None = None,
) -> int:
    """Registra una revisión declarada; no consulta internet ni autentica personas."""
    if confirmacion is not True:
        raise ValueError("Debe confirmar explícitamente la revisión de la fuente original.")
    valores = {
        "titulo": (titulo, 300), "institucion": (institucion, 160),
        "fuente": (fuente, 200), "resumen": (resumen, 4000),
        "verificado_por": (verificado_por, 120),
    }
    limpios = {}
    for nombre, (valor, limite) in valores.items():
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"El campo {nombre} es obligatorio.")
        texto = valor.strip()
        if len(texto) > limite:
            raise ValueError(f"El campo {nombre} admite hasta {limite} caracteres.")
        if any(ord(c) < 32 and c not in "\n\t" for c in texto):
            raise ValueError(f"El campo {nombre} contiene caracteres de control.")
        limpios[nombre] = texto
    if categoria not in CATEGORIAS:
        raise ValueError("Seleccione una categoría del catálogo.")
    try:
        fecha_iso = date.fromisoformat(str(fecha)).isoformat()
    except (ValueError, TypeError) as exc:
        raise ValueError("La fecha debe ser un día válido con formato AAAA-MM-DD.") from exc
    if date.fromisoformat(fecha_iso) > hoy_lima():
        raise ValueError("La fecha de publicación no puede ser futura.")
    url_limpia = validar_url(url)
    inicializar_base(ruta, cargar_ejemplos=False)
    try:
        with conectar_base(ruta) as con:
            cursor = con.execute(
                """INSERT INTO noticias
                   (titulo,institucion,categoria,fuente,fecha,url,resumen,
                    verificado_por,estado_de_verificacion)
                   VALUES (?,?,?,?,?,?,?,?,'verificado')""",
                (
                    limpios["titulo"], limpios["institucion"], categoria,
                    limpios["fuente"], fecha_iso, url_limpia,
                    limpios["resumen"], limpios["verificado_por"],
                ),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        if "noticias.url" in str(exc):
            raise NoticiaDuplicada("Esta URL ya está registrada; no se agregó otra fila.") from exc
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Ruta alternativa para oes.db")
    args = parser.parse_args()
    try:
        resultado = inicializar_base(args.db)
    except (OSError, sqlite3.Error, ErrorEsquema) as exc:
        parser.exit(1, f"No se pudo preparar la base: {exc}\n")
    print(f"Base creada: {resultado['ruta']}")
    print(f"Registros: {resultado['total']} | Nuevos: {resultado['insertados']}")
    print("Los tres ejemplos son didácticos y NO son noticias verificadas.")


if __name__ == "__main__":
    main()
