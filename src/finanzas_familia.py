"""
================================================================================
finanzas_familia.py — Orquestador del Sistema de Gestión Financiera Familiar
================================================================================
Versión:  1.0
Autor:    Plataforma MCGHR — generado con Claude.ai Pro
Ubicación: C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\finanzas_familia.py

DESCRIPCIÓN:
    Script principal de la Fase 1 de la plataforma financiera familiar.
    Importa el skill lector_correos para obtener correos, usa Claude API
    para parsear y clasificar cada uno, y persiste todo en SQLite.

    Los archivos adjuntos (PDFs, Excel) se clasifican automáticamente:
    - Confianza >= 0.85 → carpeta definitiva en OneDrive
    - Confianza entre 0.60 y 0.85 → Stage area con sugerencia
    - Confianza < 0.60 → Stage area sin clasificar

    La app_revision.py (Fase 2) permite revisar y confirmar la Stage area.

DEPENDENCIAS:
    - lector_correos.py (skill en .claude\\skills\\lector_correos\\)
    - SQLite (incluido en Python estándar)
    - anthropic, pdfplumber (pip install)

USO:
    python finanzas_familia.py                   # Últimos 7 días, todas las cuentas
    python finanzas_familia.py --dias 30         # Últimos 30 días
    python finanzas_familia.py --cuenta hernan   # Solo una cuenta
    python finanzas_familia.py --solo-pdf        # Solo procesar PDFs en Extractos
    python finanzas_familia.py --dry-run         # Simular sin escribir en BD
    python finanzas_familia.py --desde 2026-01-01 --hasta 2026-03-31
================================================================================
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Agregar skill al path ─────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).parent.parent / "config_correos.json"
if not _CONFIG_PATH.exists():
    _CONFIG_PATH = Path(__file__).parent / "config_correos.json"

with open(_CONFIG_PATH) as _f:
    _CFG_BOOT = json.load(_f)
sys.path.insert(0, _CFG_BOOT["rutas"]["skill_lector"])

from lector_correos import LectorCorreos, Correo, Adjunto  # noqa: E402

# ── Dependencias externas ─────────────────────────────────────────────────────
try:
    import anthropic
    import pdfplumber
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment
except ImportError as e:
    print(f"\nFalta dependencia: {e}")
    print("   pip install anthropic pdfplumber openpyxl\n")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def cargar_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)

CFG = cargar_config()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(CFG["rutas"]["logs"]) / f"finanzas_{datetime.now():%Y%m%d}.log",
            encoding="utf-8"
        ),
    ],
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS — SQLite
# ══════════════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS transacciones (
    id                  TEXT PRIMARY KEY,
    fecha               TEXT NOT NULL,
    mes                 TEXT,
    anio                INTEGER,
    comercio            TEXT,
    descripcion         TEXT,
    categoria           TEXT,
    subcategoria        TEXT,
    tipo                TEXT DEFAULT 'gasto',
    monto_cop           REAL,
    moneda_original     TEXT DEFAULT 'COP',
    monto_original      REAL,
    banco               TEXT,
    estado              TEXT DEFAULT 'exitoso',
    titular             TEXT,
    cuenta_email        TEXT,
    fuente              TEXT,
    confianza           REAL,
    fecha_procesado     TEXT,
    revisado_humano     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS archivos (
    id                  TEXT PRIMARY KEY,
    nombre_original     TEXT,
    ruta_actual         TEXT,
    ruta_definitiva     TEXT,
    tipo_archivo        TEXT,
    tipo_mime           TEXT,
    tamano_bytes        INTEGER,
    hash_md5            TEXT,
    estado              TEXT DEFAULT 'stage',
    clasificacion_sugerida TEXT,
    titular_sugerido    TEXT,
    banco_sugerido      TEXT,
    producto_sugerido   TEXT,
    confianza           REAL,
    id_transaccion      TEXT,
    cuenta_email        TEXT,
    fecha_correo        TEXT,
    fecha_descarga      TEXT,
    FOREIGN KEY (id_transaccion) REFERENCES transacciones(id)
);

CREATE TABLE IF NOT EXISTS correos_procesados (
    id_correo           TEXT PRIMARY KEY,
    cuenta_email        TEXT,
    fecha_correo        TEXT,
    asunto              TEXT,
    remitente           TEXT,
    fecha_procesado     TEXT,
    resultado           TEXT
);

CREATE TABLE IF NOT EXISTS reglas_clasificacion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patron_remitente    TEXT,
    patron_asunto       TEXT,
    patron_contenido    TEXT,
    categoria           TEXT,
    subcategoria        TEXT,
    titular             TEXT,
    banco               TEXT,
    producto            TEXT,
    ruta_destino        TEXT,
    confianza_minima    REAL DEFAULT 0.90,
    usos                INTEGER DEFAULT 0,
    fecha_creacion      TEXT,
    creada_por          TEXT DEFAULT 'humano'
);

CREATE TABLE IF NOT EXISTS log_ejecuciones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio        TEXT,
    fecha_fin           TEXT,
    modo                TEXT,
    cuentas_procesadas  TEXT,
    correos_leidos      INTEGER DEFAULT 0,
    tx_nuevas           INTEGER DEFAULT 0,
    archivos_stage      INTEGER DEFAULT 0,
    archivos_clasificados INTEGER DEFAULT 0,
    errores             INTEGER DEFAULT 0,
    notas               TEXT
);
"""

def obtener_db() -> sqlite3.Connection:
    ruta = Path(CFG["rutas"]["db"])
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ruta))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def ya_fue_procesado(conn: sqlite3.Connection, id_correo: str) -> bool:
    r = conn.execute(
        "SELECT 1 FROM correos_procesados WHERE id_correo = ?", (id_correo,)
    ).fetchone()
    return r is not None


def registrar_procesado(conn: sqlite3.Connection, correo: Correo, resultado: str):
    conn.execute(
        """INSERT OR IGNORE INTO correos_procesados
           (id_correo, cuenta_email, fecha_correo, asunto, remitente, fecha_procesado, resultado)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (correo.id, correo.cuenta_email, correo.fecha_str,
         correo.asunto, correo.remitente,
         datetime.now(timezone.utc).isoformat(), resultado)
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE API — Parseo y clasificación
# ══════════════════════════════════════════════════════════════════════════════

PROMPT_TRANSACCION = """Sos un experto en finanzas personales colombianas.
Analizá el siguiente correo y extraé la información financiera.
Respondé ÚNICAMENTE con JSON válido, sin texto adicional ni markdown.

Si NO hay información financiera relevante: {{"relevante": false}}

Si SÍ hay información financiera:
{{
  "relevante": true,
  "fecha": "YYYY-MM-DD",
  "monto": 12345.00,
  "moneda": "COP",
  "comercio": "Nombre del comercio",
  "categoria": "Rappi|Supermercado|Restaurante|Farmacia|Gasolina|Transporte|Suscripciones|E-commerce|Salud|Impuestos|Servicios públicos|Bancario|Inversiones|Otro",
  "subcategoria": "detalle específico",
  "tipo": "gasto|ingreso",
  "banco": "banco o medio de pago si se menciona",
  "estado": "exitoso|rechazado|pendiente",
  "descripcion": "resumen en 1 línea",
  "confianza": 0.95
}}

Correo:
{texto}
"""

PROMPT_ARCHIVO = """Sos un experto en documentos financieros colombianos.
Analizá el nombre del archivo y el texto extraído, y determiná su clasificación.
Respondé ÚNICAMENTE con JSON válido, sin texto adicional ni markdown.

{{
  "tipo_documento": "extracto_bancario|factura|recibo|estado_cuenta|otro",
  "banco": "Bancolombia|BBVA|Occidente|Nequi|InteractiveBrokers|Otro",
  "producto": "CuentaCorriente|TarjetaCredito|CuentaAhorros|Cuenta|Otro",
  "titular": "GHR|MC|desconocido",
  "periodo": "YYYY-MM o null",
  "descripcion": "qué es este documento en 1 línea",
  "confianza": 0.90
}}

Nombre del archivo: {nombre}
Texto extraído (primeras 2000 chars): {texto}
"""


def _llamar_claude(prompt: str, max_tokens: int = 600) -> Optional[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY no configurada.")
    cliente = anthropic.Anthropic(api_key=api_key)
    try:
        resp = cliente.messages.create(
            model=CFG["claude_api"]["modelo_parseo"],
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = resp.content[0].text.strip()
        texto = re.sub(r"```json|```", "", texto).strip()
        return json.loads(texto)
    except (json.JSONDecodeError, IndexError) as e:
        log.warning(f"  Error parseando respuesta Claude: {e}")
        return None
    except anthropic.APIError as e:
        log.error(f"  Error Claude API: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CLASIFICACIÓN Y ENRUTAMIENTO DE ARCHIVOS
# ══════════════════════════════════════════════════════════════════════════════

def _hash_archivo(datos: bytes) -> str:
    return hashlib.md5(datos).hexdigest()


def _texto_de_pdf(datos: bytes) -> str:
    import io
    try:
        with pdfplumber.open(io.BytesIO(datos)) as pdf:
            return " ".join(p.extract_text() or "" for p in pdf.pages)[:3000]
    except Exception:
        return ""


def _ruta_definitiva(clasificacion: dict, cfg: dict) -> Optional[Path]:
    tipo = clasificacion.get("tipo_documento", "")
    banco = clasificacion.get("banco", "")
    producto = clasificacion.get("producto", "")
    titular = clasificacion.get("titular", "desconocido")
    periodo = clasificacion.get("periodo")

    raiz = Path(cfg["rutas"]["onedrive_raiz"])

    if titular not in ("GHR", "MC"):
        return None

    if tipo == "extracto_bancario" and banco and producto:
        return raiz / titular / "Extractos" / banco / producto
    elif tipo in ("factura", "recibo") and periodo:
        return raiz / titular / "Facturas" / periodo
    elif tipo == "estado_cuenta" and periodo:
        return raiz / titular / "Extractos" / banco / producto

    return None


def procesar_adjunto(
    adjunto: Adjunto,
    correo: Correo,
    conn: sqlite3.Connection,
    cfg: dict,
    dry_run: bool,
) -> dict:
    umbral_alta = cfg["clasificacion"]["umbral_confianza_alta"]
    umbral_media = cfg["clasificacion"]["umbral_confianza_media"]

    texto_extraido = ""
    if adjunto.es_pdf():
        texto_extraido = _texto_de_pdf(adjunto.datos)

    prompt = PROMPT_ARCHIVO.format(
        nombre=adjunto.nombre,
        texto=texto_extraido[:2000] if texto_extraido else "(sin texto extraíble)"
    )
    clasificacion = _llamar_claude(prompt, max_tokens=400) or {}
    confianza = float(clasificacion.get("confianza", 0.0))

    hash_md5 = _hash_archivo(adjunto.datos)
    id_archivo = f"{hash_md5[:12]}_{adjunto.nombre[:30]}"

    existe = conn.execute(
        "SELECT ruta_actual FROM archivos WHERE hash_md5 = ?", (hash_md5,)
    ).fetchone()
    if existe:
        log.info(f"  Adjunto duplicado (ya procesado): {adjunto.nombre}")
        return {"estado": "duplicado", "ruta": existe["ruta_actual"]}

    estado_archivo = "stage"
    ruta_guardado = None

    if not dry_run:
        if confianza >= umbral_alta:
            carpeta_destino = _ruta_definitiva(clasificacion, cfg)
            if carpeta_destino:
                carpeta_destino.mkdir(parents=True, exist_ok=True)
                ruta_guardado = carpeta_destino / adjunto.nombre
                ruta_guardado.write_bytes(adjunto.datos)
                estado_archivo = "clasificado"
                log.info(f"  OK [{confianza:.0%}] {adjunto.nombre} -> {carpeta_destino.name}/")

        if estado_archivo == "stage":
            stage = Path(cfg["rutas"]["stage"])
            stage.mkdir(parents=True, exist_ok=True)
            ruta_guardado = stage / adjunto.nombre
            ruta_guardado.write_bytes(adjunto.datos)
            motivo = "confianza baja" if confianza < umbral_media else "requiere revisión"
            log.info(f"  STAGE [{confianza:.0%}] {adjunto.nombre} ({motivo})")

        conn.execute(
            """INSERT OR IGNORE INTO archivos
               (id, nombre_original, ruta_actual, tipo_archivo, tipo_mime,
                tamano_bytes, hash_md5, estado, clasificacion_sugerida,
                titular_sugerido, banco_sugerido, producto_sugerido,
                confianza, cuenta_email, fecha_correo, fecha_descarga)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                id_archivo, adjunto.nombre,
                str(ruta_guardado) if ruta_guardado else None,
                clasificacion.get("tipo_documento"),
                adjunto.tipo_mime, adjunto.tamaño_bytes, hash_md5,
                estado_archivo,
                clasificacion.get("descripcion"),
                clasificacion.get("titular"),
                clasificacion.get("banco"),
                clasificacion.get("producto"),
                confianza,
                correo.cuenta_email, correo.fecha_str,
                datetime.now(timezone.utc).isoformat(),
            )
        )

    return {
        "estado": estado_archivo,
        "confianza": confianza,
        "clasificacion": clasificacion,
        "ruta": str(ruta_guardado) if ruta_guardado else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PROCESAMIENTO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def procesar_correo(
    correo: Correo,
    filtro_categoria: str,
    conn: sqlite3.Connection,
    cfg: dict,
    dry_run: bool,
) -> dict:
    if ya_fue_procesado(conn, correo.id):
        return {"estado": "duplicado"}

    datos = _llamar_claude(PROMPT_TRANSACCION.format(texto=correo.texto_para_ia))
    resultado = {"estado": "sin_datos", "tx": None, "archivos": []}

    if datos and datos.get("relevante"):
        fecha_str = datos.get("fecha", correo.fecha_str)
        try:
            fecha = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
        except ValueError:
            fecha = correo.fecha

        monto = float(datos.get("monto", 0) or 0)
        moneda = datos.get("moneda", "COP")
        tasas = cfg["tasas_conversion"]
        monto_cop = monto * tasas.get(f"{moneda}_COP", 1) if moneda != "COP" else monto

        titular = "GHR"
        for nombre, datos_cuenta in cfg["cuentas_gmail"].items():
            if datos_cuenta["email"] == correo.cuenta_email:
                titular = datos_cuenta.get("titular", "GHR")
                break

        id_tx = hashlib.md5(
            f"{correo.id}{fecha_str}{monto}".encode()
        ).hexdigest()[:16]

        if not dry_run:
            conn.execute(
                """INSERT OR IGNORE INTO transacciones
                   (id, fecha, mes, anio, comercio, descripcion, categoria,
                    subcategoria, tipo, monto_cop, moneda_original, monto_original,
                    banco, estado, titular, cuenta_email, fuente, confianza, fecha_procesado)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    id_tx, fecha_str, fecha.strftime("%B %Y"), fecha.year,
                    datos.get("comercio"), datos.get("descripcion"),
                    datos.get("categoria", filtro_categoria),
                    datos.get("subcategoria"),
                    datos.get("tipo", "gasto"),
                    round(monto_cop, 0), moneda, monto,
                    datos.get("banco"), datos.get("estado", "exitoso"),
                    titular, correo.cuenta_email, "Gmail",
                    datos.get("confianza", 0.8),
                    datetime.now(timezone.utc).isoformat(),
                )
            )

        resultado["estado"] = "ok"
        resultado["tx"] = datos
        log.info(
            f"  OK {datos.get('comercio','?'):<30} "
            f"${monto_cop:>10,.0f} COP  "
            f"[{datos.get('confianza',0):.0%}]"
        )

    for adjunto in correo.adjuntos:
        if adjunto.es_pdf() or adjunto.es_excel():
            info_arch = procesar_adjunto(adjunto, correo, conn, cfg, dry_run)
            resultado["archivos"].append(info_arch)

    if not dry_run:
        registrar_procesado(conn, correo, resultado["estado"])
        conn.commit()

    return resultado


def construir_lectores(cfg: dict, cuentas_filtro: Optional[list] = None) -> list:
    lectores = []

    for nombre, datos in cfg.get("cuentas_gmail", {}).items():
        if not datos.get("activa", True):
            continue
        if cuentas_filtro and nombre not in cuentas_filtro:
            continue
        lectores.append(LectorCorreos({
            "tipo":             "gmail",
            "nombre":           nombre,
            "email":            datos["email"],
            "credentials_file": cfg["rutas"]["credentials_gmail"],
            "tokens_dir":       cfg["rutas"]["tokens_gmail"],
        }))

    for nombre, datos in cfg.get("cuentas_imap", {}).items():
        if not datos.get("activa", False):
            continue
        if cuentas_filtro and nombre not in cuentas_filtro:
            continue
        lectores.append(LectorCorreos({
            "tipo":      "imap",
            "nombre":    nombre,
            "email":     datos["email"],
            "servidor":  datos["servidor"],
            "puerto":    datos["puerto"],
            "ssl":       datos["ssl"],
        }))

    return lectores


def main():
    Path(CFG["rutas"]["logs"]).mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Sistema de Gestión Financiera Familiar MCGHR — Fase 1"
    )
    parser.add_argument("--dias",    type=int, default=7)
    parser.add_argument("--desde",  help="Fecha inicio YYYY-MM-DD")
    parser.add_argument("--hasta",  help="Fecha fin YYYY-MM-DD")
    parser.add_argument("--cuenta", help="Solo esta cuenta (ej: hernan)")
    parser.add_argument("--solo-pdf",   action="store_true")
    parser.add_argument("--solo-gmail", action="store_true")
    parser.add_argument("--dry-run",    action="store_true")
    args = parser.parse_args()

    fecha_desde = None
    fecha_hasta = None
    if args.desde:
        fecha_desde = datetime.strptime(args.desde, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if args.hasta:
        fecha_hasta = datetime.strptime(args.hasta, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    log.info("=" * 65)
    log.info("  PLATAFORMA FINANCIERA FAMILIAR MCGHR — Fase 1")
    log.info(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    log.info(f"  Modo: {'DRY-RUN' if args.dry_run else 'PRODUCCIÓN'}")
    if fecha_desde:
        log.info(f"  Período: {args.desde} -> {args.hasta or 'hoy'}")
    else:
        log.info(f"  Período: últimos {args.dias} días")
    log.info("=" * 65)

    conn = obtener_db()
    inicio = datetime.now(timezone.utc)
    stats = {"correos": 0, "tx_nuevas": 0, "stage": 0, "clasificados": 0, "errores": 0}

    cuentas_filtro = [args.cuenta] if args.cuenta else None

    if not args.solo_pdf:
        lectores = construir_lectores(CFG, cuentas_filtro)

        for lector in lectores:
            log.info(f"\n── Cuenta: {lector.nombre} ({lector.email})")

            for nombre_filtro, filtro in CFG["filtros_gmail"].items():
                if not filtro.get("activo", True):
                    continue

                try:
                    correos = lector.buscar(
                        query=filtro["query"],
                        dias=args.dias,
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta,
                        incluir_adjuntos=True,
                    )

                    for correo in correos:
                        stats["correos"] += 1
                        try:
                            r = procesar_correo(
                                correo, filtro["categoria"], conn, CFG, args.dry_run
                            )
                            if r["estado"] == "ok":
                                stats["tx_nuevas"] += 1
                            for arch in r.get("archivos", []):
                                if arch.get("estado") == "stage":
                                    stats["stage"] += 1
                                elif arch.get("estado") == "clasificado":
                                    stats["clasificados"] += 1
                        except Exception as e:
                            log.warning(f"  Error procesando correo {correo.id}: {e}")
                            stats["errores"] += 1

                except Exception as e:
                    log.error(f"  Error con filtro {nombre_filtro!r}: {e}")
                    stats["errores"] += 1

    fin = datetime.now(timezone.utc)
    duracion = (fin - inicio).seconds

    if not args.dry_run:
        conn.execute(
            """INSERT INTO log_ejecuciones
               (fecha_inicio, fecha_fin, modo, correos_leidos, tx_nuevas,
                archivos_stage, archivos_clasificados, errores)
               VALUES (?,?,?,?,?,?,?,?)""",
            (inicio.isoformat(), fin.isoformat(),
             "dry-run" if args.dry_run else "produccion",
             stats["correos"], stats["tx_nuevas"],
             stats["stage"], stats["clasificados"], stats["errores"])
        )
        conn.commit()

    conn.close()

    log.info("\n" + "=" * 65)
    log.info("  RESUMEN")
    log.info(f"  Correos leídos:          {stats['correos']:>6}")
    log.info(f"  Transacciones nuevas:    {stats['tx_nuevas']:>6}")
    log.info(f"  Archivos -> definitivo:  {stats['clasificados']:>6}")
    log.info(f"  Archivos -> Stage:       {stats['stage']:>6}")
    log.info(f"  Errores:                 {stats['errores']:>6}")
    log.info(f"  Duración:                {duracion}s")
    log.info(f"  {'(nada guardado — modo simulación)' if args.dry_run else 'Guardado en SQLite'}")
    log.info("=" * 65)


if __name__ == "__main__":
    main()
