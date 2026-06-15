"""
Modelo: PeriodoFinanciero

Representa el período financiero familiar: arranca ~el día 25 del mes anterior
y cierra cuando se acredita el próximo salario (fecha tentativa = día 24 del mes
corriente, confirmada cuando llega el pago real).

Ejemplo: período junio-2026 = 25-may-2026 → 24-jun-2026 (tentativa)

La fecha_fin_real se escribe cuando el ETL detecta un ingreso de tipo SALARIO
dentro del mes siguiente, confirmando el cierre del período.
"""

from sqlalchemy import Column, String, Date, Integer
from backend.models.base import Base


class PeriodoFinanciero(Base):
    __tablename__ = "periodos_financieros"

    id = Column(String, primary_key=True)            # ej: "2026-06"
    anio = Column(Integer, nullable=False)           # 2026
    mes = Column(Integer, nullable=False)            # 6  (mes de gasto)
    fecha_inicio = Column(Date, nullable=False)      # 2026-05-25
    fecha_fin_tentativa = Column(Date, nullable=False)  # 2026-06-24  ← mostrar en itálica
    fecha_fin_real = Column(Date)                    # NULL hasta confirmar salario
    estado = Column(
        String(20),
        default="abierto"
        # abierto | cerrado
        # cerrado = fecha_fin_real fue seteada
    )
    # Día del mes anterior en que llegó el salario que abrió este período.
    # Puede variar entre 23 y 27. Se completa al procesar el ingreso.
    dia_acreditacion_salario = Column(Integer)       # 25, 26, 27...
    notas = Column(String)
