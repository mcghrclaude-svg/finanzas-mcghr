"""
Database engine and session management.
Uses async SQLAlchemy with SQLite (aiosqlite driver).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.db_url,
    echo=settings.env == "dev",
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_tables():
    """Create all tables on startup. Schema managed via SQL migration scripts."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
