"""
reset_pipeline_dev.py -- Vuelve la DB de dev a un estado limpio conocido
para poder correr pruebas repetibles del pipeline ETL Gmail.

Identifica las filas creadas por el pipeline (no las de otros seeders) asi:
  - transacciones / tramos / entidades_potenciales: por el prefijo de id
    ID_PREFIJO_PIPELINE ("gmail-etl-") que correlacion.py usa para todo
    id_transaccion que crea.
  - correos_procesados: todas las filas con cuenta_gmail en ('hernan','malu')
    -- hoy nada mas escribe en esta tabla en dev.
  - log_ejecuciones: las filas cuyas notas empiezan con "ETL pipeline dev".

Tambien borra los JSON de staging/ generados por corridas anteriores.

Rechaza correr si el path de la DB no contiene "dev" (misma regla que el
resto del pipeline -- nunca tocar produccion).

Uso:
    python scripts/etl/reset_pipeline_dev.py
    python scripts/etl/reset_pipeline_dev.py --db data/dev/finanzas_dev.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DB_DEV_PATH, ID_PREFIJO_PIPELINE, STAGING_DIR, conectar_db_dev  # noqa: E402


def resetear(db_path: str) -> dict:
    conn = conectar_db_dev(db_path)
    conteos = {}

    conteos["tramos"] = conn.execute(
        "DELETE FROM tramos WHERE id_transaccion IN "
        "(SELECT id FROM transacciones WHERE id LIKE ?)",
        (f"{ID_PREFIJO_PIPELINE}%",),
    ).rowcount

    conteos["entidades_potenciales"] = conn.execute(
        "DELETE FROM entidades_potenciales WHERE id_transaccion IN "
        "(SELECT id FROM transacciones WHERE id LIKE ?)",
        (f"{ID_PREFIJO_PIPELINE}%",),
    ).rowcount

    conteos["transacciones"] = conn.execute(
        "DELETE FROM transacciones WHERE id LIKE ?", (f"{ID_PREFIJO_PIPELINE}%",)
    ).rowcount

    conteos["correos_procesados"] = conn.execute(
        "DELETE FROM correos_procesados WHERE cuenta_gmail IN ('hernan', 'malu')"
    ).rowcount

    conteos["log_ejecuciones"] = conn.execute(
        "DELETE FROM log_ejecuciones WHERE notas LIKE 'ETL pipeline dev%'"
    ).rowcount

    conn.commit()
    conn.close()
    return conteos


def limpiar_staging() -> int:
    if not STAGING_DIR.exists():
        return 0
    archivos = list(STAGING_DIR.glob("*.json"))
    for archivo in archivos:
        archivo.unlink()
    return len(archivos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resetear la DB de dev al estado limpio para el pipeline ETL")
    parser.add_argument("--db", default=str(DB_DEV_PATH))
    args = parser.parse_args()

    print(f"Reseteando pipeline ETL en {args.db}...")
    conteos = resetear(args.db)
    for tabla, cantidad in conteos.items():
        print(f"  {tabla}: {cantidad} filas borradas")

    borrados = limpiar_staging()
    print(f"  staging/: {borrados} archivos borrados")

    print("Reset completo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
