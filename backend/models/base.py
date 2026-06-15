from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Clase base para todos los modelos SQLAlchemy.
    Importada por database.py para create_tables().
    """
    pass
