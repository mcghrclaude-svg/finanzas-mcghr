"""
Lista todos los entornos de prueba registrados.

Uso:
    python scripts/env/list_envs.py
"""

import json
from pathlib import Path

ENVS_FILE = Path("data/envs.json")


def main():
    if not ENVS_FILE.exists():
        print("No hay entornos registrados. Usa create_env.py para crear uno.")
        return

    envs = json.loads(ENVS_FILE.read_text())
    if not envs:
        print("No hay entornos registrados.")
        return

    print(f"{'Nombre':<20} {'Tipo':<10} {'Creado':<25} DB")
    print("-" * 80)
    for nombre, info in envs.items():
        print(f"{nombre:<20} {info['tipo']:<10} {info['creado'][:19]:<25} {info['db_path']}")


if __name__ == "__main__":
    main()
