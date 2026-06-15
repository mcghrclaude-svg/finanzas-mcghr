"""
Resetea un entorno: elimina la DB y la vuelve a crear con datos fresh.

Uso:
    python scripts/env/reset_env.py --nombre mi_env
"""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Resetear entorno")
    parser.add_argument("--nombre", required=True)
    args = parser.parse_args()

    print(f"Reseteando entorno '{args.nombre}'...")
    subprocess.run([sys.executable, "scripts/env/destroy_env.py", "--nombre", args.nombre, "--forzar"], check=True)
    subprocess.run([sys.executable, "scripts/env/create_env.py", "--nombre", args.nombre], check=True)
    print(f"✓ Entorno '{args.nombre}' reseteado")


if __name__ == "__main__":
    main()
