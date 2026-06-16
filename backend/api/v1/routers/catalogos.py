"""
Router: /api/v1/catalogos
ABM de datos maestros: categorias, cuentas, contrapartes, personas.
Regla: nunca borrado fisico. Solo inactivacion (activa = False).
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.core.database import get_db
from backend.schemas.catalogos import (
    CategoriaCreate, CategoriaUpdate, CategoriaRead, CategoriaFlat,
    CuentaCreate, CuentaUpdate, CuentaRead,
    ContraparteCreate, ContraparteUpdate, ContraparteRead,
    PersonaCreate, PersonaUpdate, PersonaRead,
    MsgResponse,
)
from backend.repositories.catalogos_repo import (
    CategoriaRepo, CuentaRepo, ContraparteRepo, PersonaRepo
)

router = APIRouter()


# ── Categorias ────────────────────────────────────────────────────────────────

@router.get("/categorias")
async def listar_categorias(
    solo_activas: bool = Query(True),
    flat: bool = Query(False, description="true = lista plana para selects"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = CategoriaRepo(db)
    if flat:
        items = await repo.listar_flat(solo_activas)
        return [CategoriaFlat.model_validate(i).model_dump() for i in items]
    # Arbol de dicts — ya viene construido del repo
    return await repo.listar_arbol(solo_activas)


@router.get("/categorias/{categoria_id}", response_model=CategoriaFlat)
async def obtener_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    obj = await CategoriaRepo(db).get(categoria_id.upper())
    if not obj:
        raise HTTPException(404, f"Categoria '{categoria_id}' no encontrada")
    return obj


@router.post("/categorias", status_code=201)
async def crear_categoria(body: CategoriaCreate, db: AsyncSession = Depends(get_db)) -> Any:
    repo = CategoriaRepo(db)
    if await repo.get(body.id):
        raise HTTPException(409, f"Categoria '{body.id}' ya existe")
    if body.id_padre:
        padre = await repo.get(body.id_padre)
        if not padre:
            raise HTTPException(422, f"Categoria padre '{body.id_padre}' no existe")
        if padre.nivel >= 3:
            raise HTTPException(422, "No se puede anidar mas de 3 niveles")
    data = body.model_dump()
    data.pop("hijos", None)
    obj = await repo.crear(data)
    return CategoriaFlat.model_validate(obj).model_dump()


@router.patch("/categorias/{categoria_id}", response_model=CategoriaFlat)
async def editar_categoria(
    categoria_id: str, body: CategoriaUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await CategoriaRepo(db).actualizar(
        categoria_id.upper(), body.model_dump(exclude_none=True)
    )
    if not obj:
        raise HTTPException(404, f"Categoria '{categoria_id}' no encontrada")
    return obj


@router.delete("/categorias/{categoria_id}", response_model=MsgResponse)
async def inactivar_categoria(categoria_id: str, db: AsyncSession = Depends(get_db)):
    ok = await CategoriaRepo(db).inactivar(categoria_id.upper())
    if not ok:
        raise HTTPException(404, f"Categoria '{categoria_id}' no encontrada")
    return {"msg": f"Categoria '{categoria_id}' inactivada"}


# ── Cuentas ───────────────────────────────────────────────────────────────────

@router.get("/cuentas", response_model=list[CuentaRead])
async def listar_cuentas(
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return await CuentaRepo(db).listar(solo_activas=solo_activas)


@router.get("/cuentas/{cuenta_id}", response_model=CuentaRead)
async def obtener_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_db)):
    obj = await CuentaRepo(db).get(cuenta_id.upper())
    if not obj:
        raise HTTPException(404, f"Cuenta '{cuenta_id}' no encontrada")
    return obj


@router.post("/cuentas", response_model=CuentaRead, status_code=201)
async def crear_cuenta(body: CuentaCreate, db: AsyncSession = Depends(get_db)):
    repo = CuentaRepo(db)
    if await repo.get(body.id):
        raise HTTPException(409, f"Cuenta '{body.id}' ya existe")
    return await repo.crear(body.model_dump())


@router.patch("/cuentas/{cuenta_id}", response_model=CuentaRead)
async def editar_cuenta(
    cuenta_id: str, body: CuentaUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await CuentaRepo(db).actualizar(
        cuenta_id.upper(), body.model_dump(exclude_none=True)
    )
    if not obj:
        raise HTTPException(404, f"Cuenta '{cuenta_id}' no encontrada")
    return obj


@router.delete("/cuentas/{cuenta_id}", response_model=MsgResponse)
async def inactivar_cuenta(cuenta_id: str, db: AsyncSession = Depends(get_db)):
    ok = await CuentaRepo(db).inactivar(cuenta_id.upper())
    if not ok:
        raise HTTPException(404, f"Cuenta '{cuenta_id}' no encontrada")
    return {"msg": f"Cuenta '{cuenta_id}' inactivada"}


# ── Contrapartes ──────────────────────────────────────────────────────────────

@router.get("/contrapartes", response_model=list[ContraparteRead])
async def listar_contrapartes(
    tipo: str | None = Query(None),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return await ContraparteRepo(db).listar(tipo, solo_activas)


@router.get("/contrapartes/{contraparte_id}", response_model=ContraparteRead)
async def obtener_contraparte(contraparte_id: str, db: AsyncSession = Depends(get_db)):
    obj = await ContraparteRepo(db).get(contraparte_id.upper())
    if not obj:
        raise HTTPException(404, f"Contraparte '{contraparte_id}' no encontrada")
    return obj


@router.post("/contrapartes", response_model=ContraparteRead, status_code=201)
async def crear_contraparte(body: ContraparteCreate, db: AsyncSession = Depends(get_db)):
    repo = ContraparteRepo(db)
    if await repo.get(body.id):
        raise HTTPException(409, f"Contraparte '{body.id}' ya existe")
    return await repo.crear(body.model_dump())


@router.patch("/contrapartes/{contraparte_id}", response_model=ContraparteRead)
async def editar_contraparte(
    contraparte_id: str, body: ContraparteUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await ContraparteRepo(db).actualizar(
        contraparte_id.upper(), body.model_dump(exclude_none=True)
    )
    if not obj:
        raise HTTPException(404, f"Contraparte '{contraparte_id}' no encontrada")
    return obj


@router.delete("/contrapartes/{contraparte_id}", response_model=MsgResponse)
async def inactivar_contraparte(contraparte_id: str, db: AsyncSession = Depends(get_db)):
    ok = await ContraparteRepo(db).inactivar(contraparte_id.upper())
    if not ok:
        raise HTTPException(404, f"Contraparte '{contraparte_id}' no encontrada")
    return {"msg": f"Contraparte '{contraparte_id}' inactivada"}


# ── Personas ──────────────────────────────────────────────────────────────────

@router.get("/personas", response_model=list[PersonaRead])
async def listar_personas(
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    return await PersonaRepo(db).listar(solo_activas)


@router.get("/personas/{persona_id}", response_model=PersonaRead)
async def obtener_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    obj = await PersonaRepo(db).get(persona_id.upper())
    if not obj:
        raise HTTPException(404, f"Persona '{persona_id}' no encontrada")
    return obj


@router.post("/personas", response_model=PersonaRead, status_code=201)
async def crear_persona(body: PersonaCreate, db: AsyncSession = Depends(get_db)):
    repo = PersonaRepo(db)
    if await repo.get(body.id):
        raise HTTPException(409, f"Persona '{body.id}' ya existe")
    return await repo.crear(body.model_dump())


@router.patch("/personas/{persona_id}", response_model=PersonaRead)
async def editar_persona(
    persona_id: str, body: PersonaUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await PersonaRepo(db).actualizar(
        persona_id.upper(), body.model_dump(exclude_none=True)
    )
    if not obj:
        raise HTTPException(404, f"Persona '{persona_id}' no encontrada")
    return obj


@router.delete("/personas/{persona_id}", response_model=MsgResponse)
async def inactivar_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    ok = await PersonaRepo(db).inactivar(persona_id.upper())
    if not ok:
        raise HTTPException(404, f"Persona '{persona_id}' no encontrada")
    return {"msg": f"Persona '{persona_id}' inactivada"}
