"""
Router: /api/v1/transacciones
Gestion de transacciones financieras  -- el modulo central de la app.

Endpoints:
    GET    /                    Lista paginada con filtros
    POST   /                    Crear transaccion manual
    POST   /{id}/documentos     Adjuntar un archivo (factura/extracto) a la transaccion
    GET    /pendientes          Cola de confirmacion (estado=pendiente)
    GET    /{id}                Detalle de una transaccion
    PATCH  /{id}                Editar campos de una transaccion
    POST   /{id}/confirmar      Confirmar transaccion pendiente
    POST   /{id}/descartar      Descartar transaccion pendiente
    DELETE /{id}                Inactivar transaccion (soft delete)
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.exceptions import ValidationError
from backend.schemas.transacciones import TransaccionCreate, TransaccionCreateResponse
from backend.services.transacciones_service import TransaccionesService

router = APIRouter()


@router.get("/")
async def listar_transacciones(
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None),
    limit: int = Query(50, le=200),
    desde: str | None = Query(None, description="Fecha inicio YYYY-MM-DD"),
    hasta: str | None = Query(None, description="Fecha fin YYYY-MM-DD"),
    id_categoria: str | None = Query(None),
    id_cuenta: str | None = Query(None),
    quien_pago: str | None = Query(None, description="GHR | MC"),
    tipo: str | None = Query(None, description="gasto | ingreso | transferencia"),
    id_contraparte: str | None = Query(None),
    es_recurrente: bool | None = Query(None),
    estado_reembolso: str | None = Query(None),
):
    """Lista transacciones confirmadas con filtros y paginacion por cursor."""
    # TODO: implementar con TransaccionesService
    return {"items": [], "next_cursor": None, "total": 0}


@router.post("/", status_code=201, response_model=TransaccionCreateResponse)
async def crear_transaccion(
    body: TransaccionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea una transaccion manual. Va directo a estado confirmado."""
    service = TransaccionesService(db)
    resultado = await service.crear(body.model_dump())
    return TransaccionCreateResponse(**resultado)


@router.post("/{transaccion_id}/documentos", status_code=201)
async def adjuntar_documento(
    transaccion_id: str,
    file: UploadFile = File(...),
    tipo_vinculo: str = Form("factura"),
    db: AsyncSession = Depends(get_db),
):
    """Sube un archivo y lo vincula a la transaccion (factura/extracto)."""
    if not file.filename:
        raise ValidationError("El archivo no tiene nombre", field="file")

    contenido = await file.read()
    if not contenido:
        raise ValidationError("El archivo esta vacio", field="file")

    docs_dir = Path(settings.documentos_path)
    docs_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    ruta = docs_dir / f"{uuid.uuid4()}{ext}"
    ruta.write_bytes(contenido)

    service = TransaccionesService(db)
    resultado = await service.agregar_adjunto(
        tx_id=transaccion_id,
        nombre_archivo=file.filename,
        ruta=str(ruta),
        tipo_mime=file.content_type,
        tipo_vinculo=tipo_vinculo,
    )
    return resultado


@router.get("/pendientes")
async def listar_pendientes(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=200),
):
    """Cola de confirmacion  -- transacciones propuestas por el ETL pendientes de revision."""
    # TODO: implementar con TransaccionesService
    return {"items": [], "total": 0}


@router.get("/{transaccion_id}")
async def obtener_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Detalle completo de una transaccion incluyendo tramos y documentos vinculados."""
    # TODO: implementar con TransaccionesService
    raise HTTPException(status_code=404, detail="Transaccion no encontrada")


@router.patch("/{transaccion_id}")
async def editar_transaccion(
    transaccion_id: str,
    # body: TransaccionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edita campos de una transaccion. Genera entrada en reglas_clasificacion si hay correccion."""
    # TODO: implementar con TransaccionesService
    return {}


@router.post("/{transaccion_id}/confirmar")
async def confirmar_transaccion(
    transaccion_id: str,
    # body: TransaccionUpdate | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Confirma una transaccion pendiente (con o sin edicion previa)."""
    # TODO: implementar con TransaccionesService
    return {}


@router.post("/{transaccion_id}/descartar")
async def descartar_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Descarta una transaccion pendiente  -- no se registra en el sistema."""
    # TODO: implementar con TransaccionesService
    return {}


@router.delete("/{transaccion_id}")
async def inactivar_transaccion(
    transaccion_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete  -- marca la transaccion como anulada. Nunca borra datos."""
    # TODO: implementar con TransaccionesService
    return {}
