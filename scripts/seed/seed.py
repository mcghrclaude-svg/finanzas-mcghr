"""
Orquestador de seeders. Ejecuta todos en orden.

Uso:
    python scripts/seed/seed.py --env dev
    python scripts/seed/seed.py --env staging --modulos catalogos presupuestos

Orden de ejecución (respeta FK):
    1. seed_catalogos     (datos maestros: personas, categorías, cuentas, contrapartes)
    2. seed_transacciones (movimientos históricos 12 meses)
    3. seed_presupuestos  (presupuestos mensuales coherentes con transacciones)
    4. seed_obligaciones  (préstamos, servicios, recurrentes)
    5. seed_inversiones   (ahorros, acciones IBKR, inmueble en pozo)
    6. seed_inbox         (ítems pendientes de confirmación)
"""

import argparse
import sys

MODULOS = [
    "catalogos",
    "transacciones",
    "presupuestos",
    "obligaciones",
    "inversiones",
    "inbox",
]


def main():
    parser = argparse.ArgumentParser(description="Sembrar datos de prueba")
    parser.add_argument("--env", default="dev", choices=["dev", "staging"])
    parser.add_argument("--modulos", nargs="+", default=MODULOS, choices=MODULOS)
    parser.add_argument("--dry-run", action="store_true", help="Muestra qué haría sin ejecutar")
    args = parser.parse_args()

    print(f"Seeding entorno '{args.env}' — módulos: {', '.join(args.modulos)}")
    for modulo in args.modulos:
        if modulo not in args.modulos:
            continue
        mod_name = f"scripts.seed.seed_{modulo}"
        if args.dry_run:
            print(f"  [dry-run] {mod_name}")
            continue
        try:
            import importlib
            m = importlib.import_module(mod_name)
            m.run(env=args.env)
            print(f"  ✓ {modulo}")
        except Exception as e:
            print(f"  ✗ {modulo}: {e}")
            sys.exit(1)

    print("Seeding completado.")


if __name__ == "__main__":
    main()
