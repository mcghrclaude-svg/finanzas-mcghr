"""
Seeder: transacciones históricas 12 meses.

Patrón de distribución (simula familia colombiana, clase media-alta Bogotá):
    40% origen email (notificaciones bancarias)
    30% origen PDF (extractos)
    20% origen mobile (capturas iPhone)
    10% origen manual

Volumen:
    ~50-80 transacciones por mes
    Ingresos: 2-3 por mes (salarios + arriendo recibido)
    Gastos: resto

Montos orientativos (COP 2026):
    Salario GHR: 15.000.000
    Salario MC:  8.000.000
    Mercado/mes: 1.800.000
    Restaurantes/mes: 600.000
    Servicios/mes: 450.000
    Streaming/mes: 120.000

REGLA: NUNCA usar nombres reales, correos reales ni cuentas reales.
Todos los nombres de comercio son ficticios o genéricos.

TODO: implementar con factory-boy + inserción SQLAlchemy.
"""

def run(env: str = "dev"):
    meses = 12
    tx_por_mes = 65  # promedio
    print(f"  [seed_transacciones] ~{meses * tx_por_mes} transacciones (12 meses) — env={env}")
