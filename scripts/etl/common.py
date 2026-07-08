"""
common.py -- Utilidades compartidas del pipeline ETL Gmail (dev).

Todo script de este pipeline que escriba en la base de datos debe usar
validar_db_dev() o conectar_db_dev() antes de conectar. Nunca debe ser
posible que un script de este pipeline escriba en la DB de produccion
(OneDrive).

Este pipeline cubre unicamente la fuente Gmail. Las fuentes PDF (extractos
OneDrive) y JSON (PWA mobile) tienen su estructura preparada en
extraccion.py (funciones que levantan NotImplementedError) pero su logica
no forma parte de esta entrega.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DEV_PATH = REPO_ROOT / "data" / "dev" / "finanzas_dev.db"
STAGING_DIR = REPO_ROOT / "staging"
CONFIG_CORREOS_PATH = (
    Path.home() / ".claude" / "Proyectos" / "FinanzasFamilia" / "config_correos.json"
)

# Prefijo de id_transaccion para las filas insertadas por este pipeline.
# Permite a reset_pipeline_dev.py identificar y limpiar solo lo que el
# pipeline creo, sin tocar datos de otros seeders.
ID_PREFIJO_PIPELINE = "gmail-etl-"

CUENTAS_GMAIL_VALIDAS = ("hernan", "malu")


# ------------------------------------------------------------------
# Seguridad de DB -- nunca escribir en produccion
# ------------------------------------------------------------------

def validar_db_dev(db_path: Union[str, Path]) -> Path:
    """Aborta si el path de la DB no contiene 'dev'. Nunca escribir en produccion."""
    ruta = Path(db_path)
    if "dev" not in str(ruta).lower():
        raise SystemExit(
            f"ABORTADO: el path de la DB no contiene 'dev': {ruta}\n"
            f"Este pipeline solo puede escribir en la base de datos de desarrollo."
        )
    return ruta


def conectar_db_dev(db_path: Union[str, Path] = DB_DEV_PATH) -> sqlite3.Connection:
    ruta = validar_db_dev(db_path)
    if not ruta.exists():
        raise SystemExit(f"ABORTADO: no existe la DB de dev en {ruta}")
    conn = sqlite3.connect(str(ruta))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------------
# Fechas
# ------------------------------------------------------------------

def parsear_fecha_cli(valor: str, nombre_param: str) -> datetime:
    try:
        return datetime.strptime(valor, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(
            f"ERROR: {nombre_param} invalido: {valor!r}. Formato esperado: YYYY-MM-DD"
        )


# ------------------------------------------------------------------
# Deteccion de monto
# ------------------------------------------------------------------

_PATRON_MONTO = re.compile(
    r'(?:\$|COP|USD)\s*\$?\s*(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)',
    re.IGNORECASE,
)


def extraer_monto(texto: str) -> Optional[float]:
    """
    Busca un patron de monto tipo '$45.900', '$45,900', 'COP 1.234.567',
    '$1,234.56' en el texto y devuelve el valor numerico normalizado.
    Devuelve None si no encuentra ningun patron de monto.
    """
    if not texto:
        return None
    m = _PATRON_MONTO.search(texto)
    if not m:
        return None
    return _normalizar_numero(m.group(1))


def _normalizar_numero(crudo: str) -> float:
    """Normaliza un numero con separadores de miles/decimales ambiguos."""
    if "." in crudo and "," in crudo:
        if crudo.rfind(",") > crudo.rfind("."):
            # la coma esta despues -> es el separador decimal (formato europeo)
            crudo = crudo.replace(".", "").replace(",", ".")
        else:
            # el punto esta despues -> es el separador decimal (formato US)
            crudo = crudo.replace(",", "")
    elif "," in crudo:
        grupos = crudo.split(",")
        if len(grupos[-1]) == 3:
            crudo = crudo.replace(",", "")  # coma como separador de miles
        else:
            crudo = crudo.replace(",", ".")  # coma como separador decimal
    elif "." in crudo:
        grupos = crudo.split(".")
        if len(grupos[-1]) == 3:
            crudo = crudo.replace(".", "")  # punto como separador de miles
        # si el ultimo grupo no tiene 3 digitos ya es un decimal valido
    return float(crudo)


# ------------------------------------------------------------------
# Reglas de descarte de marketing / regla B
# ------------------------------------------------------------------

_REMITENTES_MARKETING = re.compile(
    r'(newsletter|marketing|promocion|promo@|noticias@|news@|info@mailer|'
    r'mailchimp|sendgrid|no-?reply-newsletter)',
    re.IGNORECASE,
)

# Palabras clave que indican que, aunque el snippet no traiga el monto,
# el correo podria ser un hecho economico real -- vale la pena revisar
# el cuerpo completo antes de descartarlo (regla B).
_KEYWORDS_REGLA_B = re.compile(
    r'(order programada|orden programada|factura|recibo|comprobante|'
    r'confirmacion de pago|pedido confirmado|pago exitoso|suscripcion|'
    r'renovacion|cargo aplicado|compra aprobada|transferencia)',
    re.IGNORECASE,
)


def es_remitente_marketing(remitente: str) -> bool:
    return bool(_REMITENTES_MARKETING.search(remitente or ""))


def es_candidato_regla_b(asunto: str, snippet: str) -> bool:
    texto = f"{asunto or ''} {snippet or ''}"
    return bool(_KEYWORDS_REGLA_B.search(texto))


# ------------------------------------------------------------------
# Staging
# ------------------------------------------------------------------

def ruta_staging_candidatos(fecha_desde: str, fecha_hasta: str) -> Path:
    STAGING_DIR.mkdir(exist_ok=True)
    return STAGING_DIR / f"candidatos_{fecha_desde}_{fecha_hasta}.json"


def ruta_staging_ambiguos(fecha_desde: str, fecha_hasta: str) -> Path:
    STAGING_DIR.mkdir(exist_ok=True)
    return STAGING_DIR / f"ambiguos_{fecha_desde}_{fecha_hasta}.json"


def cargar_config_correos(config_path: Union[str, Path] = CONFIG_CORREOS_PATH) -> dict:
    ruta = Path(config_path)
    if not ruta.exists():
        raise SystemExit(f"ERROR: no se encontro config_correos.json en {ruta}")
    return json.loads(ruta.read_text(encoding="utf-8"))
