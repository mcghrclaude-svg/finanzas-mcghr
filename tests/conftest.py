"""
Configuracion global de pytest.

Fixtures disponibles en todos los tests:
    client      AsyncClient de httpx apuntando al backend con DB en memoria
    db_session  AsyncSession de SQLAlchemy (DB en memoria)

CRITICO: importar backend.models antes de create_all para que todos los
modelos queden registrados en Base.metadata. Sin esto, create_all no
crea las tablas y los tests fallan con OperationalError.

Regla: NUNCA usar datos reales. Todos los datos son dummy.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.main import app
from backend.core.database import get_db
from backend.core.config import settings

# Forzar entorno test
settings.env = "test"
settings.db_path = ":memory:"
settings.claude_provider = "mock"
settings.mail_provider = "mock"

# CRITICO: importar todos los modelos para que Base.metadata los registre.
# La Base real esta en backend.models.base  -- NO en backend.core.database.
import backend.models  # noqa: F401   -- side-effect: registra todos los modelos
from backend.models.base import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """AsyncSession con DB en memoria, limpia por cada test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # config_pwa_import es, a proposito, una tabla sin modelo SQLAlchemy
        # (ver docstring de backend/api/v1/routers/pwa_config.py) -- create_all
        # no la crea. Se arma aca con el mismo DDL que
        # schema/init_prod_desde_cero.sql usa para bootstrapear produccion,
        # para que cualquier test que dispare la regeneracion de
        # catalogos.json (efecto secundario de escribir en el catalogo) la
        # encuentre creada, igual que en una DB real.
        await conn.execute(text("""
            CREATE TABLE config_pwa_import (
                id                  INTEGER PRIMARY KEY CHECK (id = 1),
                intervalo_minutos   INTEGER NOT NULL DEFAULT 60,
                raices              TEXT    NOT NULL DEFAULT '[]',
                actualizado_en      TEXT
            )
        """))
        await conn.execute(text(
            "INSERT INTO config_pwa_import (id, intervalo_minutos, raices) VALUES (1, 60, '[]')"
        ))

        # config_home_widgets: mismo criterio -- tabla de configuracion sin
        # modelo SQLAlchemy (ver docstring de home_config.py), se arma aca
        # con el mismo DDL que schema/finanzas_v1_8.sql.
        await conn.execute(text("""
            CREATE TABLE config_home_widgets (
                id                  INTEGER PRIMARY KEY CHECK (id = 1),
                insight_visible     BOOLEAN NOT NULL DEFAULT 1,
                patrimonio_visible  BOOLEAN NOT NULL DEFAULT 1,
                ask_visible         BOOLEAN NOT NULL DEFAULT 1
            )
        """))
        await conn.execute(text(
            "INSERT INTO config_home_widgets (id, insight_visible, patrimonio_visible, ask_visible) VALUES (1, 1, 1, 1)"
        ))

    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """AsyncClient con override de get_db para usar la sesion de test."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as c:
        yield c
    app.dependency_overrides.clear()
