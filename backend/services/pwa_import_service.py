"""
pwa_import_service -- inserta un gasto capturado por la PWA mobile como
transaccion confirmada, con el mismo patron que el alta manual de escritorio
(backend/repositories/transacciones_repository.py:crear_manual).

Decision (ver conversacion de diseno): la PWA es un canal de carga manual
de confianza equivalente al alta de escritorio, no un canal de baja confianza
como el ETL de correo/PDF. Por eso NO pasa por el Inbox -- nace ya
'confirmado', igual que crear_manual().

Usado por scripts/import_pwa_gastos.py, que es quien resuelve la sesion
async y corre este service fila por fila.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.catalogo import Categoria, Cuenta, Moneda
from backend.models.transaccion import Transaccion, Tramo
from backend.models.documento import Documento
from backend.models.vinculo import Vinculo

CAMPOS_OBLIGATORIOS = ["id", "fecha", "id_categoria", "monto", "id_moneda", "id_medio_pago", "quien"]

MAX_LEN_COMENTARIOS = 1000

DISPOSITIVO_POR_QUIEN = {
    "GHR": "iPhone_GHR",
    "MC": "iPhone_MC",
}


@dataclass
class ResultadoImport:
    ok: bool
    motivo: str = ""          # "actualizado" si ok=True y era un upsert;
                               # si ok=False: "invalido" | "error"
    detalle: str = ""
    id_transaccion: str | None = None


def validar_campos(gasto: dict[str, Any]) -> str | None:
    """Devuelve un mensaje de error si falta algo o el tipo es invalido, o None si esta OK."""
    faltantes = [c for c in CAMPOS_OBLIGATORIOS if gasto.get(c) in (None, "")]
    if faltantes:
        return f"Campos obligatorios faltantes: {', '.join(faltantes)}"

    try:
        monto = float(gasto["monto"])
    except (TypeError, ValueError):
        return f"monto invalido: {gasto.get('monto')!r}"
    if monto <= 0:
        return "monto debe ser mayor a cero"

    if gasto["quien"] not in DISPOSITIVO_POR_QUIEN:
        return f"quien invalido: {gasto.get('quien')!r} (esperado GHR o MC)"

    return None


async def validar_catalogos(db: AsyncSession, gasto: dict[str, Any]) -> str | None:
    """Verifica que id_categoria/id_moneda/id_medio_pago existan y esten activos."""
    cat = await db.get(Categoria, gasto["id_categoria"])
    if not cat or not cat.activa:
        return f"id_categoria inexistente o inactiva: {gasto['id_categoria']!r}"

    moneda = await db.get(Moneda, gasto["id_moneda"])
    if not moneda or not moneda.activa:
        return f"id_moneda inexistente o inactiva: {gasto['id_moneda']!r}"

    cuenta = await db.get(Cuenta, gasto["id_medio_pago"])
    if not cuenta or not cuenta.activa:
        return f"id_medio_pago inexistente o inactivo: {gasto['id_medio_pago']!r}"

    return None


def _normalizar_es_reembolsable(gasto: dict[str, Any]) -> bool:
    """es_reembolsable es opcional -- por compatibilidad con JSONs subidos
    antes de que este campo existiera en la PWA (ver _normalizar_comentarios)."""
    return bool(gasto.get("es_reembolsable", False))


def _normalizar_comentarios(gasto: dict[str, Any]) -> str | None:
    """comentarios es opcional -- por compatibilidad con JSONs subidos antes
    de que este campo existiera. Se trunca server-side a MAX_LEN_COMENTARIOS
    en vez de confiar solo en el maxLength del navegador: un JSON armado a
    mano, un bug futuro del cliente, o un archivo viejo corrupto podrian
    llegar a pendientes/ sin pasar por el formulario real de la PWA."""
    comentarios = gasto.get("comentarios")
    if not comentarios:
        return None
    return str(comentarios)[:MAX_LEN_COMENTARIOS]


async def importar_gasto(
    db: AsyncSession,
    gasto: dict[str, Any],
    ruta_imagen_disco: str | None,
    nombre_imagen: str | None,
    tipo_mime_imagen: str | None,
) -> ResultadoImport:
    """
    Inserta Transaccion + Tramo (+ Documento + Vinculo si hay foto).
    No hace commit -- lo maneja el caller para poder controlar la transaccion
    de archivos_mobile_procesados/log_ejecuciones_mobile junto con esta fila.
    """
    error_campos = validar_campos(gasto)
    if error_campos:
        return ResultadoImport(ok=False, motivo="invalido", detalle=error_campos)

    error_catalogos = await validar_catalogos(db, gasto)
    if error_catalogos:
        return ResultadoImport(ok=False, motivo="invalido", detalle=error_catalogos)

    id_gasto = str(gasto["id"])
    existente = await db.get(Transaccion, id_gasto)
    if existente is not None:
        return await _actualizar_gasto(db, existente, gasto)

    ahora = datetime.now(timezone.utc)
    es_reembolsable = _normalizar_es_reembolsable(gasto)

    tx = Transaccion(
        id=id_gasto,
        fecha=gasto["fecha"],
        tipo="gasto",
        descripcion=_normalizar_comentarios(gasto) or "Gasto cargado desde PWA",
        quien_pago=gasto["quien"],
        estado="confirmado",
        revisado_humano=1,
        completitud="completo",
        confianza=1.0,
        origen="mobile",
        fuente="mobile",
        id_categoria=gasto["id_categoria"],
        es_reembolsable=es_reembolsable,
        estado_reembolso="pendiente" if es_reembolsable else None,
        creado_en=ahora,
        actualizado_en=ahora,
    )
    db.add(tx)

    tramo = Tramo(
        id_transaccion=id_gasto,
        numero_orden=1,
        id_cuenta_origen=gasto["id_medio_pago"],
        monto_origen=float(gasto["monto"]),
        moneda_origen=gasto["id_moneda"],
        estado="confirmado",
    )
    db.add(tramo)

    if ruta_imagen_disco and nombre_imagen:
        doc_id = f"MOB-{id_gasto}"
        doc = Documento(
            id=doc_id,
            nombre_archivo=nombre_imagen,
            ruta=ruta_imagen_disco,
            tipo_mime=tipo_mime_imagen or "image/jpeg",
            estado="clasificado",
            origen_dispositivo=DISPOSITIVO_POR_QUIEN[gasto["quien"]],
            procesado=True,
            creado_en=ahora,
        )
        db.add(doc)

        vinculo = Vinculo(
            id_documento=doc_id,
            id_transaccion=id_gasto,
            tipo_vinculo="factura",  # CHECK constraint solo acepta factura|extracto
            confianza=1.0,
            fecha_vinculo=ahora.date().isoformat(),
            creado_por="script_import_pwa",
        )
        db.add(vinculo)

    await db.flush()
    return ResultadoImport(ok=True, id_transaccion=id_gasto)


async def _actualizar_gasto(db: AsyncSession, tx: Transaccion, gasto: dict[str, Any]) -> ResultadoImport:
    """Upsert: el id ya existe -- el usuario edito un gasto (sincronizado
    o no) desde la PWA y lo volvio a subir en un archivo nuevo (no se puede
    reescribir un JSON ya movido a procesados/). Actualiza los campos
    editables en vez de marcar duplicado sin tocar nada."""
    era_reembolsable = tx.es_reembolsable
    es_reembolsable = _normalizar_es_reembolsable(gasto)
    ahora = datetime.now(timezone.utc)

    tx.fecha = gasto["fecha"]
    tx.descripcion = _normalizar_comentarios(gasto)
    tx.id_categoria = gasto["id_categoria"]
    tx.es_reembolsable = es_reembolsable
    if not era_reembolsable and es_reembolsable:
        tx.estado_reembolso = "pendiente"
    elif not es_reembolsable:
        tx.estado_reembolso = None
    # si ya era reembolsable y lo sigue siendo, no tocar estado_reembolso
    # (puede estar en curso: solicitado/recibido).
    tx.actualizado_en = ahora

    tramo = (await db.execute(
        select(Tramo).where(Tramo.id_transaccion == tx.id, Tramo.numero_orden == 1)
    )).scalar_one_or_none()
    if tramo is not None:
        tramo.id_cuenta_origen = gasto["id_medio_pago"]
        tramo.monto_origen = float(gasto["monto"])
        tramo.moneda_origen = gasto["id_moneda"]

    await db.flush()
    return ResultadoImport(ok=True, motivo="actualizado", id_transaccion=tx.id)
