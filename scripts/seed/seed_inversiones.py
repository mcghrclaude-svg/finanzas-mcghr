"""
Seeder: inversiones y patrimonio.

Ejemplos sembrados:
    - Cuenta de ahorro CDT (AHORRO): COP 50.000.000 ficticio
    - Portafolio IBKR (ACCIONES): 3 posiciones ficticias (ETFs)
    - Apartamento en pozo (INMUEBLE): en construcción, cuotas iniciales

Valuaciones: snapshot del valor inicial + actualización mensual ficticia.

TODO: implementar.
"""

def run(env: str = "dev"):
    print(f"  [seed_inversiones] 3 activos con valuaciones históricas — env={env}")
