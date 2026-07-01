"""
Centraliza imports de modelos para que Alembic y create_all los detecten.
"""
from backend.models.base import Base  # noqa: F401
from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona, EntidadPotencial  # noqa: F401
from backend.models.transaccion import Transaccion, Tramo, Asiento  # noqa: F401
from backend.models.presupuesto import Presupuesto  # noqa: F401
from backend.models.obligacion import Obligacion  # noqa: F401
from backend.models.inversion import Inversion, Posicion, Valuacion  # noqa: F401
from backend.models.documento import Documento  # noqa: F401
from backend.models.inbox import InboxMobile  # noqa: F401
from backend.models.regla import ReglaClasificacion  # noqa: F401  — fix: era "Regla"
from backend.models.periodo import PeriodoFinanciero  # noqa: F401
from backend.models.velocidad_historica import VelocidadHistorica  # noqa: F401
