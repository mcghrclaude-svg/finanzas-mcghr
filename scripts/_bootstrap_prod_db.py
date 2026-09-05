r"""
Script de un solo uso: inicializa Prod/finanzas.db desde cero.

1. Corre Base.metadata.create_all() (todas las tablas modeladas en SQLAlchemy).
2. Aplica schema/init_prod_desde_cero.sql (tablas/vistas que solo existen
   como SQL crudo: config_pwa_import, archivos_mobile_procesados,
   log_ejecuciones_mobile, correos_procesados, log_ejecuciones, vistas).

Ejecucion (ENV_FILE debe apuntar a .env.prod; -m es obligatorio -- correrlo
como script directo (python scripts\_bootstrap_prod_db.py) no agrega la raiz
del repo a sys.path y "backend" no se puede importar, ver ModuleNotFoundError):
    $env:ENV_FILE = ".env.prod"
    .\venv\Scripts\python.exe -m scripts._bootstrap_prod_db
"""
import asyncio
import os
import sqlite3


async def crear_tablas_orm():
    from backend.core.database import engine
    from backend.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def aplicar_script_sql():
    from backend.core.config import settings
    con = sqlite3.connect(settings.db_path)
    con.executescript(open("schema/init_prod_desde_cero.sql", encoding="utf-8").read())
    con.commit()
    con.close()


if __name__ == "__main__":
    if os.environ.get("ENV_FILE") != ".env.prod":
        raise SystemExit("Corre esto con ENV_FILE=.env.prod (ver docstring).")
    asyncio.run(crear_tablas_orm())
    print("Tablas ORM creadas.")
    aplicar_script_sql()
    print("Script init_prod_desde_cero.sql aplicado.")
