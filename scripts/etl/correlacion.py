"""
correlacion.py -- Paso 2 del pipeline ETL Gmail (dev).

Recibe el JSON de staging producido por extraccion.py y:
  Capa 1 (dedup):       descarta message_id ya vistos en correos_procesados.
  Capa 2 (correlacion): busca si el hecho economico ya existe en la DB por
                         otro canal (mismo titular, monto +/-1%, fecha +/-3 dias).

DECISION DE DISENO (zero candidatos != ambiguo):
    Cuando la busqueda de correlacion no encuentra NINGUN candidato, este
    es el caso normal de un hecho economico visto por primera vez -- se
    crea una transaccion nueva directamente, no se manda a "ambiguos".
    El bucket de ambiguos es solo para MULTIPLES candidatos sin forma de
    decidir cual es el correcto. Si "cero candidatos" tambien fuera a
    ambiguos, todo primer evento (la inmensa mayoria de los casos) quedaria
    trabado esperando resolucion manual, lo cual no es el comportamiento
    esperado (ver escenarios b, c, e, f en docs/ESCENARIOS_PRUEBA_ETL.md).

Solo escribe en la DB de desarrollo (validado por common.conectar_db_dev).

Uso:
    python scripts/etl/correlacion.py --input staging/candidatos_2026-06-01_2026-06-30.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    CONFIG_CORREOS_PATH,
    DB_DEV_PATH,
    ID_PREFIJO_PIPELINE,
    STAGING_DIR,
    cargar_config_correos,
    conectar_db_dev,
)

BANCOS_CONOCIDOS = ["Bancolombia", "BBVA", "Banco de Occidente", "Nequi"]

_PATRON_COMERCIO = re.compile(
    r'\ben\s+([A-Z][A-Z0-9\.\-\s]{2,40}?)(?=\s*(?:\n|Tarjeta|Fecha|Lugar|\.|$))'
)

# ------------------------------------------------------------------
# Confianza -- heuristica documentada regla por regla
# ------------------------------------------------------------------

# Base segun tipo de fuente: un SMS reenviado (subject = codigo corto del
# banco, ej. "891333") es una notificacion directa del banco al celular
# del titular -- mas confiable que un correo de comercio/marketing que
# puede tener texto libre y formatos variables.
BASE_CONFIANZA_SMS_REENVIADO = 0.80
BASE_CONFIANZA_CORREO_COMERCIO = 0.65

# Bono: si el evento correlaciona limpiamente con otro ya existente (dos
# fuentes independientes describen el mismo hecho), eso es evidencia
# fuerte de que los datos son correctos.
BONO_CORRELACION_LIMPIA = 0.15

# Penalizacion: si el catalogo no tiene la cuenta/contraparte y hubo que
# proponer una entidad potencial, hay informacion sin confirmar por un
# humano -- baja la confianza.
PENALIZACION_ENTIDAD_POTENCIAL = 0.10

# Penalizacion: si el monto no estaba en el snippet y se extrajo leyendo
# el cuerpo completo (regla B), la deteccion es menos directa/mas fragil.
PENALIZACION_LECTURA_FALLBACK = 0.05


def detectar_tipo_fuente(candidato: dict) -> str:
    """Un SMS reenviado tiene como asunto el codigo corto del banco (ej. '891333')."""
    asunto = (candidato.get("asunto") or "").strip()
    if re.fullmatch(r"\d{4,8}", asunto):
        return "sms_reenviado"
    return "correo_comercio"


def calcular_confianza(tipo_fuente: str, hubo_correlacion_limpia: bool,
                        cantidad_entidades_potenciales: int,
                        necesito_lectura_completa: bool) -> float:
    base = BASE_CONFIANZA_SMS_REENVIADO if tipo_fuente == "sms_reenviado" else BASE_CONFIANZA_CORREO_COMERCIO
    confianza = base
    if hubo_correlacion_limpia:
        confianza += BONO_CORRELACION_LIMPIA
    if cantidad_entidades_potenciales > 0:
        confianza -= PENALIZACION_ENTIDAD_POTENCIAL
    if necesito_lectura_completa:
        confianza -= PENALIZACION_LECTURA_FALLBACK
    return max(0.0, min(1.0, round(confianza, 4)))


# ------------------------------------------------------------------
# Completitud (TEXT segun ADR-008) -- misma escala que ETL_PROMPT paso 1f
# ------------------------------------------------------------------

def calcular_completitud(fecha: Optional[str], monto: Optional[float],
                          id_categoria: Optional[str], id_cuenta: Optional[str]) -> str:
    campos = [fecha, monto, id_categoria, id_cuenta]
    presentes = sum(1 for c in campos if c is not None)
    score = presentes * 0.25
    if score >= 1.0:
        return "completo"
    if score >= 0.75:
        return "parcial"
    return "minimo"


# ------------------------------------------------------------------
# Extraccion liviana de banco / comercio del texto del correo
# ------------------------------------------------------------------

def detectar_banco(texto: str) -> Optional[str]:
    texto_low = (texto or "").lower()
    for banco in BANCOS_CONOCIDOS:
        clave = banco.lower().replace("banco de ", "")
        if clave in texto_low:
            return banco
    return None


def extraer_comercio(texto: str) -> Optional[str]:
    if not texto:
        return None
    m = _PATRON_COMERCIO.search(texto)
    return m.group(1).strip() if m else None


def proponer_clasificacion(remitente: str, asunto: str, filtros_gmail: dict) -> dict:
    """Reusa los filtros ya curados en config_correos.json (filtros_gmail)
    para proponer categoria/contraparte cuando el remitente matchea un
    canal conocido (ej. Netflix, Spotify). No reemplaza clasificacion por
    LLM -- es solo un mapeo de canal->etiqueta ya definido por el usuario."""
    texto = f"{remitente or ''} {asunto or ''}".lower()
    for clave, filtro in (filtros_gmail or {}).items():
        raiz = re.sub(r"_(email|sms)$", "", clave)
        if raiz and raiz in texto:
            return {"categoria": filtro.get("categoria"), "contraparte": filtro.get("subcategoria") or clave}
    return {"categoria": None, "contraparte": None}


def resolver_contraparte(conn, nombre_propuesto: Optional[str]) -> Optional[str]:
    if not nombre_propuesto:
        return None
    propuesto_low = nombre_propuesto.lower()
    for row in conn.execute("SELECT id, nombre FROM contrapartes WHERE activa = 1"):
        if row["nombre"].lower() in propuesto_low:
            return row["id"]
    return None


def resolver_cuenta(conn, banco: Optional[str], titular: str, es_tarjeta: bool) -> Optional[str]:
    if not banco:
        return None
    tipo_buscado = "TC" if es_tarjeta else "CC"
    row = conn.execute(
        "SELECT id FROM cuentas WHERE activa = 1 AND banco LIKE ? AND nombre LIKE ? AND tipo = ?",
        (f"%{banco}%", f"%{titular}%", tipo_buscado),
    ).fetchone()
    return row["id"] if row else None


def crear_entidad_potencial(conn, tipo: str, valor_propuesto: str, id_transaccion: str) -> None:
    conn.execute(
        "INSERT INTO entidades_potenciales (tipo, valor_propuesto, id_transaccion, estado, creado_en) "
        "VALUES (?, ?, ?, 'pendiente', ?)",
        (tipo, valor_propuesto, id_transaccion, datetime.now(timezone.utc).isoformat()),
    )


def registrar_correo_procesado(conn, candidato: dict, resultado: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO correos_procesados
            (id_correo, cuenta_gmail, fecha_correo, asunto, remitente, fecha_procesado, resultado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (candidato["message_id"], candidato["cuenta"], candidato["fecha"], candidato.get("asunto", ""),
         candidato.get("remitente", ""), datetime.now(timezone.utc).isoformat(), resultado),
    )


# ------------------------------------------------------------------
# Procesamiento de un candidato
# ------------------------------------------------------------------

def procesar_candidato(conn, candidato: dict, filtros_gmail: dict, cuentas_gmail_cfg: dict,
                        stats: dict, ambiguos: list) -> None:
    msg_id = candidato["message_id"]
    cuenta = candidato["cuenta"]
    titular = cuentas_gmail_cfg[cuenta]["titular"]

    # Capa 1 -- dedup determinista por message_id
    if conn.execute("SELECT 1 FROM correos_procesados WHERE id_correo = ?", (msg_id,)).fetchone():
        stats["ya_procesados"] += 1
        return

    if candidato.get("descartable"):
        registrar_correo_procesado(conn, candidato, "descartado")
        stats["descartados"] += 1
        return

    texto_completo = candidato.get("snippet_o_cuerpo") or ""
    monto = candidato.get("monto_detectado")
    fecha_evento = candidato["fecha"][:10]  # YYYY-MM-DD

    banco = detectar_banco(f"{candidato.get('remitente','')} {candidato.get('asunto','')} {texto_completo}")
    comercio = extraer_comercio(texto_completo)
    es_tarjeta = "tarjeta" in texto_completo.lower()
    es_ingreso = bool(re.search(r"recibid[oa]|ingreso", texto_completo, re.IGNORECASE))
    tipo_tx = "ingreso" if es_ingreso else "gasto"
    moneda = "USD" if re.search(r"\bUSD\b", texto_completo) else "COP"

    clasif = proponer_clasificacion(candidato.get("remitente", ""), candidato.get("asunto", ""), filtros_gmail)
    contraparte_propuesta = comercio or clasif.get("contraparte")

    # Capa 2 -- correlacion (solo si hay monto: sin monto no hay rango que buscar)
    candidatos_correlacion = []
    if monto is not None:
        candidatos_correlacion = conn.execute(
            """
            SELECT t.id, t.id_evento
            FROM transacciones t
            JOIN tramos tr ON t.id = tr.id_transaccion AND tr.numero_orden = 1
            WHERE t.quien_pago = ?
              AND t.fecha BETWEEN date(?, '-3 days') AND date(?, '+3 days')
              AND tr.monto_origen BETWEEN ? AND ?
            """,
            (titular, fecha_evento, fecha_evento, monto * 0.99, monto * 1.01),
        ).fetchall()

    if len(candidatos_correlacion) > 1:
        ambiguos.append({
            "message_id": msg_id,
            "cuenta": cuenta,
            "fecha": candidato["fecha"],
            "monto_detectado": monto,
            "motivo": "multiples_candidatos",
            "candidatos": [dict(r) for r in candidatos_correlacion],
        })
        registrar_correo_procesado(conn, candidato, "ambiguo")
        stats["ambiguos"] += 1
        return

    id_contraparte = resolver_contraparte(conn, contraparte_propuesta)
    id_cuenta = resolver_cuenta(conn, banco, titular, es_tarjeta)
    entidades_creadas: list[str] = []

    if len(candidatos_correlacion) == 1:
        _fusionar_con_existente(
            conn, candidatos_correlacion[0], candidato, id_contraparte, id_cuenta,
            contraparte_propuesta, banco, titular, es_tarjeta, entidades_creadas,
        )
        stats["enriquecidas"] += 1
    else:
        _crear_nueva(
            conn, candidato, tipo_tx, moneda, monto, fecha_evento, titular, cuenta,
            id_contraparte, id_cuenta, contraparte_propuesta, banco, es_tarjeta, entidades_creadas,
        )
        stats["nuevas"] += 1

    stats["entidades_potenciales"] += len(entidades_creadas)
    registrar_correo_procesado(conn, candidato, "ok")


def _fusionar_con_existente(conn, existente, candidato: dict, id_contraparte: Optional[str],
                             id_cuenta: Optional[str], contraparte_propuesta: Optional[str],
                             banco: Optional[str], titular: str, es_tarjeta: bool,
                             entidades_creadas: list) -> None:
    tx_id = existente["id"]
    id_evento = existente["id_evento"] or f"EVT_{uuid.uuid4().hex[:16]}"
    if not existente["id_evento"]:
        conn.execute("UPDATE transacciones SET id_evento = ? WHERE id = ?", (id_evento, tx_id))

    if contraparte_propuesta and id_contraparte is None:
        crear_entidad_potencial(conn, "contraparte", contraparte_propuesta, tx_id)
        entidades_creadas.append("contraparte")
    if banco and id_cuenta is None:
        crear_entidad_potencial(conn, "cuenta", f"{banco} ({'TC' if es_tarjeta else 'CC'}) {titular}", tx_id)
        entidades_creadas.append("cuenta")

    completitud = calcular_completitud(candidato["fecha"][:10], candidato.get("monto_detectado"), None, id_cuenta)
    confianza = calcular_confianza(
        detectar_tipo_fuente(candidato), True, len(entidades_creadas), bool(candidato.get("necesito_lectura_completa")),
    )
    ahora = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE transacciones SET
            id_contraparte = COALESCE(id_contraparte, ?),
            confianza = MAX(confianza, ?),
            completitud = ?,
            estado_enriquecimiento = 'enriquecido',
            actualizado_en = ?
        WHERE id = ?
        """,
        (id_contraparte, confianza, completitud, ahora, tx_id),
    )
    if id_cuenta:
        conn.execute(
            "UPDATE tramos SET id_cuenta_origen = COALESCE(id_cuenta_origen, ?) "
            "WHERE id_transaccion = ? AND numero_orden = 1",
            (id_cuenta, tx_id),
        )


def _crear_nueva(conn, candidato: dict, tipo_tx: str, moneda: str, monto: Optional[float],
                  fecha_evento: str, titular: str, cuenta: str, id_contraparte: Optional[str],
                  id_cuenta: Optional[str], contraparte_propuesta: Optional[str], banco: Optional[str],
                  es_tarjeta: bool, entidades_creadas: list) -> None:
    tx_id = f"{ID_PREFIJO_PIPELINE}{uuid.uuid4().hex[:12]}"
    id_evento = f"EVT_{uuid.uuid4().hex[:16]}"

    # entidades_potenciales.id_transaccion tiene FK contra transacciones.id
    # -- hay que crear la transaccion primero, las entidades despues.
    creara_entidad_contraparte = bool(contraparte_propuesta and id_contraparte is None)
    creara_entidad_cuenta = bool(banco and id_cuenta is None)
    if creara_entidad_contraparte:
        entidades_creadas.append("contraparte")
    if creara_entidad_cuenta:
        entidades_creadas.append("cuenta")

    # id_categoria no se clasifica en este pipeline heuristico (sin LLM) --
    # queda para revision humana desde el inbox, o para el ETL real de
    # Claude Desktop en produccion.
    completitud = calcular_completitud(fecha_evento, monto, None, id_cuenta)
    confianza = calcular_confianza(
        detectar_tipo_fuente(candidato), False, len(entidades_creadas), bool(candidato.get("necesito_lectura_completa")),
    )
    ahora = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO transacciones
            (id, fecha, fecha_hora, tipo, descripcion, estado, confianza, revisado_humano,
             completitud, id_contraparte, quien_pago, fuente, id_correo, origen,
             id_evento, estado_enriquecimiento, creado_en, actualizado_en)
        VALUES (?, ?, ?, ?, ?, 'pendiente', ?, 0, ?, ?, ?, ?, ?, 'email', ?, 'inicial', ?, ?)
        """,
        (tx_id, fecha_evento, candidato["fecha"], tipo_tx, candidato.get("asunto", ""), confianza,
         completitud, id_contraparte, titular, f"gmail_{cuenta}", candidato["message_id"], id_evento, ahora, ahora),
    )

    if monto is not None:
        conn.execute(
            """
            INSERT INTO tramos (id_transaccion, numero_orden, id_cuenta_origen, monto_origen, moneda_origen, estado)
            VALUES (?, 1, ?, ?, ?, 'pendiente')
            """,
            (tx_id, id_cuenta, monto, moneda),
        )

    if creara_entidad_contraparte:
        crear_entidad_potencial(conn, "contraparte", contraparte_propuesta, tx_id)
    if creara_entidad_cuenta:
        crear_entidad_potencial(conn, "cuenta", f"{banco} ({'TC' if es_tarjeta else 'CC'}) {titular}", tx_id)


# ------------------------------------------------------------------
# Orquestacion
# ------------------------------------------------------------------

def ruta_ambiguos_desde_input(input_path: Path) -> Path:
    nombre = input_path.name
    if nombre.startswith("candidatos_"):
        return input_path.with_name(nombre.replace("candidatos_", "ambiguos_", 1))
    STAGING_DIR.mkdir(exist_ok=True)
    return STAGING_DIR / f"ambiguos_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Paso 2 del pipeline ETL: dedup + correlacion + insercion")
    parser.add_argument("--input", required=True, help="JSON de staging producido por extraccion.py")
    parser.add_argument("--db", default=str(DB_DEV_PATH), help="Path a la DB de dev")
    parser.add_argument("--config", default=str(CONFIG_CORREOS_PATH))
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"ERROR: no existe el archivo de entrada {input_path}")
    candidatos = json.loads(input_path.read_text(encoding="utf-8"))

    config = cargar_config_correos(args.config)
    filtros_gmail = config.get("filtros_gmail", {})
    cuentas_gmail_cfg = config.get("cuentas_gmail", {})

    conn = conectar_db_dev(args.db)

    stats = {"ya_procesados": 0, "descartados": 0, "nuevas": 0, "enriquecidas": 0,
              "ambiguos": 0, "entidades_potenciales": 0, "errores": 0}
    errores: list[dict] = []
    ambiguos: list[dict] = []

    ahora_inicio = datetime.now(timezone.utc).isoformat()
    cur_log = conn.execute(
        "INSERT INTO log_ejecuciones (fecha_inicio, correos_leidos, transacciones_nuevas, "
        "documentos_nuevos, alertas, notas) VALUES (?, 0, 0, 0, '{}', ?)",
        (ahora_inicio, f"ETL pipeline dev iniciado (fuente=gmail, input={input_path.name})"),
    )
    log_id = cur_log.lastrowid

    for candidato in candidatos:
        try:
            procesar_candidato(conn, candidato, filtros_gmail, cuentas_gmail_cfg, stats, ambiguos)
        except Exception as e:
            # Regla critica: un error puntual no aborta la corrida completa.
            stats["errores"] += 1
            errores.append({"message_id": candidato.get("message_id"), "error": str(e)})
            print(f"[correlacion] ERROR procesando {candidato.get('message_id')}: {e}", file=sys.stderr)
            continue

    if ambiguos:
        ruta_ambig = ruta_ambiguos_desde_input(input_path)
        existentes = json.loads(ruta_ambig.read_text(encoding="utf-8")) if ruta_ambig.exists() else []
        ruta_ambig.write_text(json.dumps(existentes + ambiguos, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[correlacion] {len(ambiguos)} casos ambiguos escritos en {ruta_ambig}")

    ahora_fin = datetime.now(timezone.utc).isoformat()
    total_procesados = len(candidatos) - stats["ya_procesados"]
    resumen = (
        f"ETL pipeline dev completado. Candidatos: {len(candidatos)}. "
        f"Nuevas: {stats['nuevas']}. Enriquecidas: {stats['enriquecidas']}. "
        f"Descartadas: {stats['descartados']}. Ambiguas: {stats['ambiguos']}. "
        f"Ya procesadas (dedup): {stats['ya_procesados']}. "
        f"Entidades potenciales: {stats['entidades_potenciales']}. Errores: {stats['errores']}."
    )
    conn.execute(
        "UPDATE log_ejecuciones SET fecha_fin = ?, correos_leidos = ?, transacciones_nuevas = ?, "
        "transacciones_enriquecidas = ?, alertas = ?, notas = ? WHERE id = ?",
        (ahora_fin, total_procesados, stats["nuevas"], stats["enriquecidas"],
         json.dumps({"stats": stats, "errores": errores}, ensure_ascii=False), resumen, log_id),
    )
    conn.commit()
    conn.close()

    print(f"[correlacion] {resumen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
