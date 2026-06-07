"""
================================================================================
auditor_correos.py — Detector de gaps en clasificación financiera
================================================================================
Versión:  1.0
Autor:    Plataforma MCGHR
Ubicación: C:\\Users\\ghriz\\.claude\\Proyectos\\FinanzasFamilia\\auditor_correos.py

DESCRIPCIÓN:
    Lee todos los correos de las cuentas configuradas SIN aplicar los filtros
    específicos de finanzas_familia.py. Usa Claude API para detectar correos
    financieramente relevantes que los filtros actuales NO estarían capturando.

    Genera un reporte con:
    - Correos financieros no capturados
    - Filtros sugeridos para agregar a config_correos.json
    - Estadísticas de cobertura actual

USO:
    python auditor_correos.py --dias 30
    python auditor_correos.py --dias 30 --cuenta hernan
    python auditor_correos.py --dias 30 --output reporte_auditoria.json
================================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_CONFIG_PATH = Path(__file__).parent / "config_correos.json"
with open(_CONFIG_PATH) as _f:
    _CFG_BOOT = json.load(_f)
sys.path.insert(0, _CFG_BOOT["rutas"]["skill_lector"])

from lector_correos import LectorCorreos  # noqa: E402

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PROMPT_AUDITORIA = """Sos un experto en finanzas personales colombianas.
Analizá este correo y determiná si contiene información financiera relevante
que debería ser capturada por un sistema de tracking de gastos.

Respondé ÚNICAMENTE con JSON válido, sin texto adicional:
{{
  "es_financiero": true|false,
  "tipo": "gasto|ingreso|transferencia|extracto|factura|impuesto|inversion|suscripcion|otro",
  "comercio_o_entidad": "nombre",
  "monto_aproximado": 12345.00 o null,
  "moneda": "COP|USD|EUR",
  "remitente_pattern": "patrón del remitente para filtro (ej: from:banco@email.com)",
  "asunto_pattern": "patrón del asunto para filtro (ej: subject:pago)",
  "categoria_sugerida": "categoría del gasto",
  "razon": "por qué es o no es financiero relevante"
}}

Correo:
{texto}
"""


def obtener_queries_actuales(cfg: dict) -> set:
    """Extrae todos los remitentes ya monitoreados de los filtros actuales."""
    monitoreados = set()
    for filtro in cfg.get("filtros_gmail", {}).values():
        query = filtro.get("query", "")
        for match in re.finditer(r'from:(\S+)', query):
            monitoreados.add(match.group(1).lower())
    return monitoreados


def auditar_cuenta(
    lector: LectorCorreos,
    dias: int,
    queries_actuales: set,
    cfg: dict,
) -> list[dict]:
    """
    Lee todos los correos de una cuenta y detecta los financieros
    que no están siendo capturados.
    """
    queries_amplias = [
        "category:purchases",
        "subject:factura OR subject:invoice OR subject:recibo OR subject:receipt",
        "subject:pago OR subject:cobro OR subject:cargo OR subject:transaccion",
        "subject:extracto OR subject:estado OR subject:cuenta",
        "subject:compra OR subject:pedido OR subject:orden",
    ]

    correos_candidatos = {}
    for q in queries_amplias:
        try:
            correos = lector.buscar(query=q, dias=dias, incluir_adjuntos=False)
            for c in correos:
                correos_candidatos[c.id] = c
        except Exception as e:
            log.warning(f"  Error con query {q!r}: {e}")

    log.info(f"  [{lector.nombre}] {len(correos_candidatos)} correos candidatos únicos")

    no_capturados = []
    for correo in correos_candidatos.values():
        remitente_lower = correo.remitente.lower()
        ya_capturado = any(q in remitente_lower for q in queries_actuales)
        if not ya_capturado:
            no_capturados.append(correo)

    log.info(f"  [{lector.nombre}] {len(no_capturados)} correos potencialmente no capturados")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    cliente = anthropic.Anthropic(api_key=api_key)
    hallazgos = []

    for correo in no_capturados[:50]:
        try:
            resp = cliente.messages.create(
                model=cfg["claude_api"]["modelo_parseo"],
                max_tokens=400,
                messages=[{
                    "role": "user",
                    "content": PROMPT_AUDITORIA.format(texto=correo.texto_para_ia)
                }],
            )
            texto = resp.content[0].text.strip()
            texto = re.sub(r"```json|```", "", texto).strip()
            analisis = json.loads(texto)

            if analisis.get("es_financiero"):
                hallazgos.append({
                    "cuenta":    lector.email,
                    "correo_id": correo.id,
                    "fecha":     correo.fecha_str,
                    "remitente": correo.remitente,
                    "asunto":    correo.asunto,
                    "analisis":  analisis,
                })
                log.info(
                    f"  GAP: {correo.remitente[:40]:<40} | "
                    f"{analisis.get('tipo','?')} | "
                    f"{analisis.get('comercio_o_entidad','?')}"
                )
        except Exception as e:
            log.warning(f"  Error analizando correo {correo.id}: {e}")

    return hallazgos


def generar_filtros_sugeridos(hallazgos: list[dict]) -> list[dict]:
    """Agrupa hallazgos por patrón y genera filtros sugeridos."""
    por_patron = defaultdict(list)
    for h in hallazgos:
        patron = h["analisis"].get("remitente_pattern", "")
        if patron:
            por_patron[patron].append(h)

    sugerencias = []
    for patron, casos in sorted(por_patron.items(), key=lambda x: -len(x[1])):
        primer_caso = casos[0]["analisis"]
        sugerencias.append({
            "frecuencia":   len(casos),
            "query":        patron,
            "categoria":    primer_caso.get("categoria_sugerida", "Otro"),
            "tipo":         primer_caso.get("tipo", "gasto"),
            "comercio":     primer_caso.get("comercio_o_entidad", ""),
            "ejemplo_asunto": casos[0]["asunto"],
            "ejemplo_remitente": casos[0]["remitente"],
            "agregar_a_config": {
                "query":     f"{patron} {primer_caso.get('asunto_pattern', '')}".strip(),
                "categoria": primer_caso.get("categoria_sugerida", "Otro"),
                "subcategoria": primer_caso.get("comercio_o_entidad", ""),
                "titular_default": "GHR",
                "activo": True,
            }
        })

    return sorted(sugerencias, key=lambda x: -x["frecuencia"])


def main():
    parser = argparse.ArgumentParser(
        description="Auditor de gaps en clasificación financiera"
    )
    parser.add_argument("--dias",    type=int, default=30)
    parser.add_argument("--cuenta",  help="Solo esta cuenta")
    parser.add_argument("--output",  help="Guardar reporte en JSON")
    args = parser.parse_args()

    with open(_CONFIG_PATH) as f:
        cfg = json.load(f)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY no configurada")
        sys.exit(1)

    log.info("=" * 65)
    log.info("  AUDITOR DE CORREOS — Detección de gaps")
    log.info(f"  Período: últimos {args.dias} días")
    log.info("=" * 65)

    queries_actuales = obtener_queries_actuales(cfg)
    log.info(f"  Filtros actuales monitoreando: {len(queries_actuales)} patrones")

    todos_hallazgos = []
    cuentas_filtro = [args.cuenta] if args.cuenta else None

    for nombre, datos in cfg.get("cuentas_gmail", {}).items():
        if not datos.get("activa", True):
            continue
        if cuentas_filtro and nombre not in cuentas_filtro:
            continue

        log.info(f"\n── Auditando: {nombre} ({datos['email']})")
        lector = LectorCorreos({
            "tipo":             "gmail",
            "nombre":           nombre,
            "email":            datos["email"],
            "credentials_file": cfg["rutas"]["credentials_gmail"],
            "tokens_dir":       cfg["rutas"]["tokens_gmail"],
        })
        hallazgos = auditar_cuenta(lector, args.dias, queries_actuales, cfg)
        todos_hallazgos.extend(hallazgos)

    sugerencias = generar_filtros_sugeridos(todos_hallazgos)

    reporte = {
        "fecha_auditoria": datetime.now(timezone.utc).isoformat(),
        "dias_analizados": args.dias,
        "total_gaps": len(todos_hallazgos),
        "filtros_sugeridos": sugerencias,
        "detalle_correos": todos_hallazgos,
    }

    log.info("\n" + "=" * 65)
    log.info(f"  RESULTADO: {len(todos_hallazgos)} correos financieros no capturados")
    log.info(f"  Filtros sugeridos: {len(sugerencias)}")

    if sugerencias:
        log.info("\n  TOP FILTROS SUGERIDOS:")
        for s in sugerencias[:5]:
            log.info(
                f"  [{s['frecuencia']}x] {s['comercio']:<30} "
                f"| {s['categoria']} | {s['query']}"
            )

    if args.output:
        salida = Path(args.output)
        salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2))
        log.info(f"\n  Reporte guardado en: {salida}")
    else:
        print("\n" + json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
