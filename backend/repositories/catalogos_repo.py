"""
Repository para catalogos maestros.
Usa los modelos de backend/models/catalogo.py sin modificarlos.
Regla: nunca borrado fisico. Solo inactivacion (activa = False).

NOTA: Categoria no tiene relationship "hijos" declarado en el modelo.
El arbol se construye manualmente desde la lista plana.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.models.catalogo import Categoria, Cuenta, Contraparte, Persona


# ── Helpers ───────────────────────────────────────────────────────────────────

def _construir_arbol(plana: list[Categoria]) -> list[dict]:
    """
    Convierte una lista plana de Categoria en arbol de dicts anidados.
    No requiere relationship en el modelo.
    """
    por_id = {}
    for c in plana:
        por_id[c.id] = {
            "id": c.id,
            "nombre": c.nombre,
            "nivel": c.nivel,
            "id_padre": c.id_padre,
            "activa": c.activa,
            "tipo_patron_gasto": c.tipo_patron_gasto,
            "hijos": [],
        }

    raices = []
    for nodo in por_id.values():
        if nodo["id_padre"] and nodo["id_padre"] in por_id:
            por_id[nodo["id_padre"]]["hijos"].append(nodo)
        else:
            raices.append(nodo)

    return raices


# ── Categoria ─────────────────────────────────────────────────────────────────

class CategoriaRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _listar_plana(self, solo_activas: bool = True) -> list[Categoria]:
        q = select(Categoria).order_by(Categoria.nivel, Categoria.id)
        if solo_activas:
            q = q.where(Categoria.activa == True)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def listar_arbol(self, solo_activas: bool = True) -> list[dict]:
        plana = await self._listar_plana(solo_activas)
        return _construir_arbol(plana)

    async def listar_flat(self, solo_activas: bool = True) -> list[Categoria]:
        return await self._listar_plana(solo_activas)

    async def get(self, id: str) -> Optional[Categoria]:
        result = await self.db.execute(
            select(Categoria).where(Categoria.id == id)
        )
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> Categoria:
        # Remover "hijos" si viene del schema antes de crear el objeto
        data.pop("hijos", None)
        obj = Categoria(**data)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def actualizar(self, id: str, data: dict) -> Optional[Categoria]:
        obj = await self.get(id)
        if not obj:
            return None
        data.pop("hijos", None)
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.db.flush()
        return obj

    async def inactivar(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        obj.activa = False
        # Inactivar hijos en cascada via query directa
        hijos = await self.db.execute(
            select(Categoria).where(Categoria.id_padre == id)
        )
        for hijo in hijos.scalars().all():
            hijo.activa = False
            # Nivel 3
            nietos = await self.db.execute(
                select(Categoria).where(Categoria.id_padre == hijo.id)
            )
            for nieto in nietos.scalars().all():
                nieto.activa = False
        await self.db.flush()
        return True


# ── Cuenta ────────────────────────────────────────────────────────────────────

class CuentaRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(self, titular: Optional[str] = None, solo_activas: bool = True) -> list[Cuenta]:
        q = select(Cuenta)
        if solo_activas:
            q = q.where(Cuenta.activa == True)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get(self, id: str) -> Optional[Cuenta]:
        result = await self.db.execute(select(Cuenta).where(Cuenta.id == id))
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> Cuenta:
        obj = Cuenta(**data)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def actualizar(self, id: str, data: dict) -> Optional[Cuenta]:
        obj = await self.get(id)
        if not obj:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.db.flush()
        return obj

    async def inactivar(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        obj.activa = False
        await self.db.flush()
        return True


# ── Contraparte ───────────────────────────────────────────────────────────────

class ContraparteRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(self, tipo: Optional[str] = None, solo_activas: bool = True) -> list[Contraparte]:
        q = select(Contraparte)
        if solo_activas:
            q = q.where(Contraparte.activa == True)
        if tipo:
            q = q.where(Contraparte.tipo == tipo)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get(self, id: str) -> Optional[Contraparte]:
        result = await self.db.execute(select(Contraparte).where(Contraparte.id == id))
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> Contraparte:
        obj = Contraparte(**data)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def actualizar(self, id: str, data: dict) -> Optional[Contraparte]:
        obj = await self.get(id)
        if not obj:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.db.flush()
        return obj

    async def inactivar(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        obj.activa = False
        await self.db.flush()
        return True


# ── Persona ───────────────────────────────────────────────────────────────────

class PersonaRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(self, solo_activas: bool = True) -> list[Persona]:
        q = select(Persona)
        if solo_activas:
            q = q.where(Persona.activa == True)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get(self, id: str) -> Optional[Persona]:
        result = await self.db.execute(select(Persona).where(Persona.id == id))
        return result.scalar_one_or_none()

    async def crear(self, data: dict) -> Persona:
        obj = Persona(**data)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def actualizar(self, id: str, data: dict) -> Optional[Persona]:
        obj = await self.get(id)
        if not obj:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.db.flush()
        return obj

    async def inactivar(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        obj.activa = False
        await self.db.flush()
        return True
