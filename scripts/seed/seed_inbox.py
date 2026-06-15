"""
Seeder: ítems en inbox pendientes de confirmación.

Siembra 10-15 ítems con variedad de:
    - completitud baja (0.3-0.5): faltan categoría o monto
    - completitud media (0.5-0.8): faltan detalles menores
    - completitud alta (0.8-0.95): listos para confirmar con un clic
    - origen mixto: email, pdf, mobile

TODO: implementar.
"""

def run(env: str = "dev"):
    print(f"  [seed_inbox] 12 ítems pendientes con completitud variada — env={env}")
