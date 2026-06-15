"""
Elimina un entorno de prueba.

Uso:
    python scripts/env/destroy_env.py --nombre mi_env
    python scripts/env/destroy_env.py --nombre mi_env --forzar

SEGURIDAD: nunca opera sobre entornos con tipo=prod.
"""

import argparse
import json
import shutil
from pathlib import Path

ENVS_FILE = Path("data/envs.json")


def main():
    parser = argparse.ArgumentParser(description="Eliminar entorno de prueba")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--forzar", action="store_true", help="Sin confirmación interactiva")
    args = parser.parse_args()

    if not ENVS_FILE.exists():
        print("No hay entornos registrados.")
        return 1

    envs = json.loads(ENVS_FILE.read_text())
    if args.nombre not in envs:
        print(f"Entorno '{args.nombre}' no encontrado.")
        return 1

    env = envs[args.nombre]
    if env["tipo"] == "prod":
        print("ERROR: no se puede eliminar un entorno de producción con este script.")
        return 1

    if not args.forzar:
        confirm = input(f"¿Eliminar entorno '{args.nombre}'? [s/N]: ")
        if confirm.lower() != "s":
            print("Cancelado.")
            return 0

    carpeta = Path(f"data/{args.nombre}")
    if carpeta.exists():
        shutil.rmtree(carpeta)
        print(f"✓ Carpeta {carpeta} eliminada")

    del envs[args.nombre]
    ENVS_FILE.write_text(json.dumps(envs, indent=2, ensure_ascii=False))
    print(f"✓ Entorno '{args.nombre}' eliminado")
    return 0


if __name__ == "__main__":
    exit(main())
