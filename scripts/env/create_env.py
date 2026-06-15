"""
Crea un entorno de prueba aislado.

Uso:
    python scripts/env/create_env.py --nombre mi_env --tipo dev
    python scripts/env/create_env.py --nombre sprint3 --tipo staging

Qué hace:
    1. Crea carpeta data/{nombre}/
    2. Crea DB SQLite vacía con schema v1.1
    3. Ejecuta seeders según el tipo
    4. Registra el entorno en data/envs.json
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

ENVS_FILE = Path("data/envs.json")
TIPOS_VALIDOS = ["dev", "test", "staging"]


def main():
    parser = argparse.ArgumentParser(description="Crear entorno de prueba")
    parser.add_argument("--nombre", required=True, help="Nombre del entorno")
    parser.add_argument("--tipo", default="dev", choices=TIPOS_VALIDOS)
    args = parser.parse_args()

    carpeta = Path(f"data/{args.nombre}")
    if carpeta.exists():
        print(f"ERROR: ya existe el entorno '{args.nombre}'. Usa reset_env.py para reiniciarlo.")
        return 1

    # Estructura de carpetas
    (carpeta / "backups").mkdir(parents=True)
    (carpeta / "onedrive" / "Inbox").mkdir(parents=True)
    (carpeta / "onedrive" / "Stage").mkdir(parents=True)
    print(f"✓ Carpetas creadas en {carpeta}")

    # TODO: crear DB con schema v1.1
    # TODO: ejecutar seeders según tipo

    # Registrar en envs.json
    ENVS_FILE.parent.mkdir(exist_ok=True)
    envs = json.loads(ENVS_FILE.read_text()) if ENVS_FILE.exists() else {}
    envs[args.nombre] = {
        "tipo": args.tipo,
        "creado": datetime.now().isoformat(),
        "db_path": str(carpeta / "finanzas.db"),
    }
    ENVS_FILE.write_text(json.dumps(envs, indent=2, ensure_ascii=False))
    print(f"✓ Entorno '{args.nombre}' ({args.tipo}) registrado")
    return 0


if __name__ == "__main__":
    exit(main())
