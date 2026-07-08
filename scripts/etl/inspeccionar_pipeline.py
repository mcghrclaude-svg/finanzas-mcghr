"""
inspeccionar_pipeline.py -- Reporte de consola del estado del pipeline ETL
Gmail en dev, sin tener que escribir SQL a mano ni abrir JSON/logs sueltos.

Muestra:
  1. Corridas registradas en log_ejecuciones (con resumen y errores si los hubo)
  2. correos_procesados agrupados por resultado y por cuenta
  3. Transacciones pendientes creadas por el pipeline (confianza, completitud)
  4. Entidades potenciales generadas, por tipo y estado
  5. Casos en el bucket de ambiguos (staging/ambiguos_*.json), por motivo

Uso:
    python scripts/etl/inspeccionar_pipeline.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DB_DEV_PATH, ID_PREFIJO_PIPELINE, STAGING_DIR, conectar_db_dev  # noqa: E402


def _titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")


def reportar_corridas(conn, limite: int = 10) -> None:
    _titulo("Corridas (log_ejecuciones)")
    filas = conn.execute(
        "SELECT * FROM log_ejecuciones WHERE notas LIKE 'ETL pipeline dev%' "
        "ORDER BY fecha_inicio DESC LIMIT ?",
        (limite,),
    ).fetchall()
    if not filas:
        print("  (sin corridas registradas)")
        return

    for fila in filas:
        print(f"  [{fila['fecha_inicio']}] -> [{fila['fecha_fin'] or 'EN CURSO'}]")
        print(f"    {fila['notas']}")
        try:
            alertas = json.loads(fila["alertas"] or "{}")
        except json.JSONDecodeError:
            alertas = {}
        errores = alertas.get("errores") or []
        if errores:
            print(f"    ERRORES ({len(errores)}):")
            for err in errores:
                print(f"      - {err.get('message_id')}: {err.get('error')}")


def reportar_correos_procesados(conn) -> None:
    _titulo("correos_procesados")
    filas = conn.execute(
        "SELECT cuenta_gmail, resultado, COUNT(*) as n FROM correos_procesados "
        "GROUP BY cuenta_gmail, resultado ORDER BY cuenta_gmail, resultado"
    ).fetchall()
    if not filas:
        print("  (vacio)")
        return
    for fila in filas:
        print(f"  {fila['cuenta_gmail']:<10} {fila['resultado']:<12} {fila['n']}")


def reportar_transacciones_pendientes(conn) -> None:
    _titulo("Transacciones pendientes creadas por el pipeline")
    filas = conn.execute(
        """
        SELECT t.id, t.fecha, t.descripcion, t.confianza, t.completitud,
               t.estado_enriquecimiento, cp.nombre as contraparte, tr.monto_origen, tr.moneda_origen
        FROM transacciones t
        LEFT JOIN contrapartes cp ON t.id_contraparte = cp.id
        LEFT JOIN tramos tr ON t.id = tr.id_transaccion AND tr.numero_orden = 1
        WHERE t.id LIKE ? AND t.estado = 'pendiente'
        ORDER BY t.creado_en DESC
        """,
        (f"{ID_PREFIJO_PIPELINE}%",),
    ).fetchall()
    print(f"  Total: {len(filas)}")
    for fila in filas:
        monto = f"{fila['monto_origen']:,.0f} {fila['moneda_origen']}" if fila["monto_origen"] is not None else "sin monto"
        contraparte = fila["contraparte"] or "(sin resolver)"
        completitud = fila["completitud"] or "(sin dato)"
        estado_enriq = fila["estado_enriquecimiento"] or "(sin dato)"
        confianza = f"{fila['confianza']:.2f}" if fila["confianza"] is not None else "(sin dato)"
        print(
            f"  {fila['id']:<24} {fila['fecha']} conf={confianza} "
            f"completitud={completitud:<9} estado={estado_enriq:<11} "
            f"{contraparte:<15} {monto}  -- {fila['descripcion']}"
        )


def reportar_entidades_potenciales(conn) -> None:
    _titulo("Entidades potenciales generadas por el pipeline")
    filas = conn.execute(
        """
        SELECT ep.tipo, ep.estado, COUNT(*) as n
        FROM entidades_potenciales ep
        JOIN transacciones t ON ep.id_transaccion = t.id
        WHERE t.id LIKE ?
        GROUP BY ep.tipo, ep.estado
        ORDER BY ep.tipo, ep.estado
        """,
        (f"{ID_PREFIJO_PIPELINE}%",),
    ).fetchall()
    if not filas:
        print("  (ninguna)")
        return
    for fila in filas:
        print(f"  {fila['tipo']:<12} {fila['estado']:<10} {fila['n']}")

    print("  Detalle:")
    detalle = conn.execute(
        """
        SELECT ep.tipo, ep.valor_propuesto, ep.estado, ep.id_transaccion
        FROM entidades_potenciales ep
        JOIN transacciones t ON ep.id_transaccion = t.id
        WHERE t.id LIKE ?
        ORDER BY ep.creado_en DESC
        """,
        (f"{ID_PREFIJO_PIPELINE}%",),
    ).fetchall()
    for fila in detalle:
        print(f"    [{fila['tipo']}] {fila['valor_propuesto']!r} ({fila['estado']}) -> {fila['id_transaccion']}")


def reportar_ambiguos() -> None:
    _titulo("Bucket de ambiguos (staging/ambiguos_*.json)")
    if not STAGING_DIR.exists():
        print("  (sin staging/)")
        return
    archivos = sorted(STAGING_DIR.glob("ambiguos_*.json"))
    if not archivos:
        print("  (ningun archivo de ambiguos)")
        return

    por_motivo: dict[str, int] = {}
    total = 0
    for archivo in archivos:
        try:
            casos = json.loads(archivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for caso in casos:
            motivo = caso.get("motivo", "desconocido")
            por_motivo[motivo] = por_motivo.get(motivo, 0) + 1
            total += 1

    print(f"  Total casos ambiguos: {total} (en {len(archivos)} archivo(s))")
    for motivo, cantidad in sorted(por_motivo.items()):
        print(f"    {motivo}: {cantidad}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reporte de estado del pipeline ETL Gmail en dev")
    parser.add_argument("--db", default=str(DB_DEV_PATH))
    args = parser.parse_args()

    conn = conectar_db_dev(args.db)
    reportar_corridas(conn)
    reportar_correos_procesados(conn)
    reportar_transacciones_pendientes(conn)
    reportar_entidades_potenciales(conn)
    reportar_ambiguos()
    conn.close()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
