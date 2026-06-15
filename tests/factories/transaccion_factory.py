"""
Factory-boy factories para datos de test.

REGLA CRÍTICA: Faker usa locale 'es_CO' (Colombia).
NUNCA usar emails reales, tokens OAuth, números de cuenta, RUTs.
Todos los datos son ficticios y solo sirven para tests.
"""

import factory
import factory.fuzzy
from faker import Faker
from decimal import Decimal
from datetime import datetime, timezone

fake = Faker('es_CO')

# IDs de categorías ficticias (deben existir en seed_catalogos de test)
CATEGORIAS_TEST = ['ALI-001', 'TRA-001', 'ENT-001', 'SAL-001', 'HOG-001']
CUENTAS_TEST = ['BCO-CC-GHR', 'BCO-TC-GHR', 'BBVA-CC-GHR']
PERSONAS_TEST = ['GHR', 'MC']


class TransaccionFactory(factory.Factory):
    class Meta:
        # No usa SQLAlchemy directamente — genera dicts para el API
        exclude = ['_model']
        model = dict

    id = factory.LazyFunction(lambda: fake.uuid4())
    fecha = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    monto = factory.LazyFunction(lambda: float(round(Decimal(str(fake.random_number(digits=5))) / 100, 2)))
    moneda = 'COP'
    tipo = factory.fuzzy.FuzzyChoice(['GASTO', 'INGRESO'])
    descripcion = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
    id_categoria = factory.fuzzy.FuzzyChoice(CATEGORIAS_TEST)
    id_cuenta = factory.fuzzy.FuzzyChoice(CUENTAS_TEST)
    id_persona = factory.fuzzy.FuzzyChoice(PERSONAS_TEST)
    origen = 'manual'
    es_recurrente = False
    es_reembolsable = False


class TransaccionGastoFactory(TransaccionFactory):
    tipo = 'GASTO'
    monto = factory.LazyFunction(lambda: float(round(Decimal(str(fake.random_int(5000, 500000))), -2)))


class TransaccionIngresoFactory(TransaccionFactory):
    tipo = 'INGRESO'
    monto = factory.LazyFunction(lambda: float(round(Decimal(str(fake.random_int(1_000_000, 15_000_000))), -3)))
