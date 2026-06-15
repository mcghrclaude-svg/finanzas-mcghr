"""
Configuración global de pytest.

Fixtures disponibles en todos los tests:
    client          AsyncClient de httpx apuntando al backend con DB en memoria
    db_session      AsyncSession de SQLAlchemy (DB en memoria)
    seed_catalogos  Carga categorías, cuentas, contrapartes, personas base

Regla: NUNCA usar datos reales (emails, tokens, RUTs, cuentas bancarias).
Todos los datos vienen de los factories de factory-boy con Faker.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.main import app
from backend.core.database import get_db, Base
from backend.core.config import settings

# Forzar entorno test
settings.env = "test"
settings.db_path = ":memory:"
settings.claude_provider = "mock"
settings.mail_provider = "mock"

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """AsyncSession con DB en memoria, limpia por cada test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """AsyncClient con override de get_db para usar la sesión de test."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
