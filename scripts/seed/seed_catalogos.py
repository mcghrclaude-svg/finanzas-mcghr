"""
Seeder: datos maestros del sistema.

Siembra:
    - 2 personas (GHR, MC)
    - ~20 categorías en 3 niveles (gastos colombianos típicos)
    - 5 cuentas (Bancolombia CC, Bancolombia TC, BBVA CC, BBVA TC, Nequi)
    - 15 contrapartes frecuentes (ficticias)
    - 15 reglas de clasificación base

TODO: implementar inserciones SQLAlchemy.
"""

CATEGORIAS = [
    # (id, nombre, nivel, id_padre)
    ("HOG",     "Hogar",              1, None),
    ("HOG-ARR", "Arriendo",           2, "HOG"),
    ("HOG-SRV", "Servicios públicos", 2, "HOG"),
    ("HOG-SRV-LUZ", "Luz",           3, "HOG-SRV"),
    ("HOG-SRV-GAS", "Gas",           3, "HOG-SRV"),
    ("HOG-SRV-INT", "Internet",      3, "HOG-SRV"),
    ("ALI",     "Alimentación",       1, None),
    ("ALI-MER", "Mercado",            2, "ALI"),
    ("ALI-REST","Restaurantes",       2, "ALI"),
    ("ALI-DOM", "Domicilios",         2, "ALI"),
    ("TRA",     "Transporte",         1, None),
    ("TRA-CAR", "Gasolina",           2, "TRA"),
    ("TRA-PAR", "Parqueadero",        2, "TRA"),
    ("TRA-APP", "Apps (Uber/Cabify)", 2, "TRA"),
    ("SAL",     "Salud",              1, None),
    ("SAL-SEG", "Seguro médico",      2, "SAL"),
    ("SAL-MED", "Medicamentos",       2, "SAL"),
    ("ENT",     "Entretenimiento",    1, None),
    ("ENT-STR", "Streaming",          2, "ENT"),
    ("ENT-OCI", "Ocio",               2, "ENT"),
    ("ING",     "Ingresos",           1, None),
    ("ING-SAL", "Salarios",           2, "ING"),
    ("ING-ARR", "Arriendo recibido",  2, "ING"),
]

CUENTAS = [
    # (id, nombre, tipo, banco, moneda, es_corporativa)
    ("BCO-CC-GHR",  "Bancolombia CC GHR",  "CC",     "Bancolombia", "COP", False),
    ("BCO-TC-GHR",  "Bancolombia TC GHR",  "TC",     "Bancolombia", "COP", False),
    ("BBVA-CC-GHR", "BBVA CC GHR",         "CC",     "BBVA",        "COP", False),
    ("BBVA-TC-GHR", "BBVA TC GHR",         "TC",     "BBVA",        "COP", False),
    ("NEQ-GHR",     "Nequi GHR",           "DIGITAL","Nequi",       "COP", False),
    ("IBKR-GHR",    "InteractiveBrokers",  "INVERSION","IBKR",     "USD", False),
]

REGLAS_BASE = [
    # (patron, id_categoria, fuente, peso)
    (r"NETFLIX.*",           "ENT-STR", "sistema", 10),
    (r"SPOTIFY.*",           "ENT-STR", "sistema", 10),
    (r"RAPPI.*",             "ALI-DOM", "sistema", 9),
    (r"UBER.*|CABIFY.*",     "TRA-APP", "sistema", 9),
    (r"TERPEL.*|PRIMAX.*",   "TRA-CAR", "sistema", 8),
    (r"EXITO.*|JUMBO.*",     "ALI-MER", "sistema", 8),
    (r"CLARO.*|MOVISTAR.*",  "HOG-SRV", "sistema", 7),
]


def run(env: str = "dev"):
    """TODO: implementar inserción SQLAlchemy en la DB del entorno."""
    print(f"  [seed_catalogos] {len(CATEGORIAS)} categorías, {len(CUENTAS)} cuentas, {len(REGLAS_BASE)} reglas — env={env}")
