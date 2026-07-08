"""
extraccion.py -- Paso 1 del pipeline ETL Gmail (dev).

Lee correos financieros de Gmail (hernan, malu) en un rango de fechas
explicito, aplica deteccion de monto por regex y reglas de descarte de
marketing, y deja un JSON de staging con los candidatos para que
correlacion.py los procese.

No escribe en la base de datos -- eso lo hace correlacion.py. No marca
correos como leidos (LectorCorreos nunca lo hace).

Uso:
    python scripts/etl/extraccion.py --fecha-desde 2026-06-01 --fecha-hasta 2026-06-30
    python scripts/etl/extraccion.py --fecha-desde 2026-06-01 --fecha-hasta 2026-06-30 --cuentas hernan

El rango de fechas es SIEMPRE obligatorio -- no hay default silencioso.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "lector_correos"))

from common import (  # noqa: E402
    CONFIG_CORREOS_PATH,
    CUENTAS_GMAIL_VALIDAS,
    cargar_config_correos,
    es_candidato_regla_b,
    es_remitente_marketing,
    extraer_monto,
    parsear_fecha_cli,
    ruta_staging_candidatos,
)

# Remitentes/palabras clave de interes financiero -- misma lista que
# paso 1a de docs/ETL_PROMPT_CLAUDE_DESKTOP.md.
QUERY_FINANCIERA = (
    "from:(bancolombia OR bbva OR occidente OR nequi OR rappi OR uber OR "
    "netflix OR spotify OR disney OR claro OR epm OR amazon)"
)


def _config_cuenta_gmail(config: dict, nombre: str) -> dict:
    cuentas = config.get("cuentas_gmail", {})
    if nombre not in cuentas or not cuentas[nombre].get("activa", True):
        raise SystemExit(f"ERROR: cuenta Gmail '{nombre}' no existe o esta inactiva en config_correos.json")
    rutas = config.get("rutas", {})
    return {
        "tipo": "gmail",
        "nombre": nombre,
        "email": cuentas[nombre]["email"],
        "credentials_file": rutas.get("credentials_gmail", ""),
        "tokens_dir": rutas.get("tokens_gmail", ""),
    }


def _procesar_correo(correo, cuenta: str) -> dict:
    """
    Aplica regex de monto + reglas de descarte de marketing + regla B
    a un correo ya descargado (con snippet y texto_plano completos).
    """
    monto = extraer_monto(correo.snippet)
    necesito_lectura_completa = False
    texto_usado = correo.snippet
    descartable = False
    motivo = "monto_en_snippet"

    if monto is None:
        if es_remitente_marketing(correo.remitente):
            descartable = True
            motivo = "remitente_marketing"
        elif es_candidato_regla_b(correo.asunto, correo.snippet):
            # Regla B: el snippet no trae el monto pero el correo podria
            # ser un hecho economico real (ej. "Order Programada",
            # facturas). LectorCorreos ya trajo el cuerpo completo
            # (texto_plano) en la misma llamada -- no hace falta una
            # segunda lectura de red.
            monto = extraer_monto(correo.texto_plano)
            necesito_lectura_completa = True
            if monto is not None:
                texto_usado = correo.texto_plano[:4000]
                motivo = "monto_en_cuerpo_completo"
            else:
                descartable = True
                motivo = "sin_monto_ni_en_cuerpo_completo"
        else:
            descartable = True
            motivo = "sin_patron_monto"

    return {
        "message_id": correo.id,
        "cuenta": cuenta,
        "fecha": correo.fecha.isoformat(),
        "remitente": correo.remitente,
        "asunto": correo.asunto,
        "monto_detectado": monto,
        "snippet_o_cuerpo": texto_usado,
        "necesito_lectura_completa": necesito_lectura_completa,
        "descartable": descartable,
        "motivo": motivo,
    }


def extraer_gmail(fecha_desde_str: str, fecha_hasta_str: str, cuentas: list[str],
                   config_path: Path) -> list[dict]:
    from lector_correos import LectorCorreos

    fecha_desde = parsear_fecha_cli(fecha_desde_str, "--fecha-desde")
    fecha_hasta = parsear_fecha_cli(fecha_hasta_str, "--fecha-hasta")
    if fecha_hasta < fecha_desde:
        raise SystemExit("ERROR: --fecha-hasta no puede ser anterior a --fecha-desde")

    config = cargar_config_correos(config_path)
    candidatos = []

    for cuenta in cuentas:
        print(f"[extraccion] Buscando correos de '{cuenta}' entre {fecha_desde_str} y {fecha_hasta_str}...")
        cuenta_cfg = _config_cuenta_gmail(config, cuenta)
        lector = LectorCorreos(cuenta_cfg)
        correos = lector.buscar(
            query=QUERY_FINANCIERA,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta + timedelta(days=1),  # 'before' es exclusivo en Gmail
            incluir_adjuntos=False,
        )
        print(f"[extraccion]   {len(correos)} correos encontrados en '{cuenta}'")

        for correo in correos:
            candidatos.append(_procesar_correo(correo, cuenta))

    return candidatos


def extraer_pdf(fecha_desde_str: str, fecha_hasta_str: str) -> list[dict]:
    """
    Extraccion desde PDFs de extractos en OneDrive.
    Fuera del alcance de esta sesion (solo Gmail). Estructura preparada
    para no tener que reordenar el CLI cuando se implemente.
    """
    raise NotImplementedError(
        "Fuente 'pdf' (extractos OneDrive) no implementada en esta entrega -- "
        "ver docs/ETL_DISENO_FUNCIONAL.md seccion 'PDFs en OneDrive'."
    )


def extraer_json_pwa(fecha_desde_str: str, fecha_hasta_str: str) -> list[dict]:
    """
    Extraccion desde JSONs de la PWA mobile (inbox foto_factura).
    Fuera del alcance de esta sesion (solo Gmail). Estructura preparada
    para no tener que reordenar el CLI cuando se implemente.
    """
    raise NotImplementedError(
        "Fuente 'json' (PWA mobile) no implementada en esta entrega -- "
        "ver docs/ETL_DISENO_FUNCIONAL.md seccion 'JSONs de la PWA'."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Paso 1 del pipeline ETL: extraccion de candidatos")
    parser.add_argument("--fecha-desde", required=True, help="YYYY-MM-DD (obligatorio, sin default)")
    parser.add_argument("--fecha-hasta", required=True, help="YYYY-MM-DD (obligatorio, sin default)")
    parser.add_argument("--fuente", default="gmail", choices=["gmail", "pdf", "json"])
    parser.add_argument("--cuentas", default="hernan,malu", help="Lista separada por comas")
    parser.add_argument("--config", default=str(CONFIG_CORREOS_PATH), help="Ruta a config_correos.json")
    parser.add_argument("--output", default=None, help="Override de la ruta de salida")
    args = parser.parse_args()

    if args.fuente == "pdf":
        extraer_pdf(args.fecha_desde, args.fecha_hasta)
        return 1
    if args.fuente == "json":
        extraer_json_pwa(args.fecha_desde, args.fecha_hasta)
        return 1

    cuentas = [c.strip() for c in args.cuentas.split(",") if c.strip()]
    for c in cuentas:
        if c not in CUENTAS_GMAIL_VALIDAS:
            raise SystemExit(f"ERROR: cuenta '{c}' invalida. Validas: {CUENTAS_GMAIL_VALIDAS}")

    try:
        candidatos = extraer_gmail(args.fecha_desde, args.fecha_hasta, cuentas, Path(args.config))
    except Exception as e:
        print(f"[extraccion] ERROR: {e}", file=sys.stderr)
        return 1

    salida = Path(args.output) if args.output else ruta_staging_candidatos(args.fecha_desde, args.fecha_hasta)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(candidatos, indent=2, ensure_ascii=False), encoding="utf-8")

    total = len(candidatos)
    descartados = sum(1 for c in candidatos if c["descartable"])
    print(f"[extraccion] {total} candidatos totales, {descartados} descartables, {total - descartados} a correlacionar")
    print(f"[extraccion] Salida: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
