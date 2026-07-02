"""
Router: /api/v1/tools
Herramientas de administracion del entorno de desarrollo.

GUARD: todos los endpoints retornan 403 si settings.env != 'dev'.
Este router NO debe registrarse ni ser accesible en produccion.
"""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db, engine
from backend.models.transaccion import Transaccion, Tramo
from backend.models.documento import Documento
from backend.models.vinculo import Vinculo
from backend.models.catalogo import EntidadPotencial

router = APIRouter()

SNAPSHOT_DIR = Path("data/dev/snapshots")

# Orden de borrado respeta dependencias (hijos antes que padres)
TABLAS_ETL = [
    "entidades_potenciales",
    "vinculos",
    "asientos",
    "tramos",
    "transacciones",
    "documentos",
    "inbox_mobile",
    "correos_procesados",
    "archivos_mobile_procesados",
    "log_ejecuciones",
]

TABLAS_CATALOGO = [
    "posiciones",
    "valuaciones",
    "inversiones",
    "obligaciones",
    "presupuestos",
    "velocidad_historica",
    "personas",
    "contrapartes",
    "cuentas",
    "categorias",
]


def _guard_dev():
    if settings.env != "dev":
        raise HTTPException(status_code=403, detail="Solo disponible en entorno dev")


# ---------------------------------------------------------------------------
# POST /tools/reset-parcial
# ---------------------------------------------------------------------------

@router.post("/reset-parcial")
async def reset_parcial(db: AsyncSession = Depends(get_db)):
    """Vacia tablas ETL. Preserva catalogo y config."""
    _guard_dev()
    counts = {}
    for tabla in TABLAS_ETL:
        r = await db.execute(text(f"DELETE FROM {tabla}"))
        counts[tabla] = r.rowcount
    await db.commit()
    return {"ok": True, "tablas_vaciadas": counts}


# ---------------------------------------------------------------------------
# POST /tools/reset-total
# ---------------------------------------------------------------------------

@router.post("/reset-total")
async def reset_total(db: AsyncSession = Depends(get_db)):
    """Vacia ETL + catalogo. Preserva reglas_clasificacion y periodos_financieros."""
    _guard_dev()
    counts = {}
    for tabla in TABLAS_ETL + TABLAS_CATALOGO:
        r = await db.execute(text(f"DELETE FROM {tabla}"))
        counts[tabla] = r.rowcount
    await db.commit()
    return {"ok": True, "tablas_vaciadas": counts}


# ---------------------------------------------------------------------------
# POST /tools/backup
# ---------------------------------------------------------------------------

class BackupRequest(BaseModel):
    carpeta: str = ""


@router.post("/backup", status_code=201)
async def backup(body: BackupRequest = BackupRequest()):
    """Copia finanzas_dev.db a la carpeta de snapshots con timestamp."""
    _guard_dev()
    dest_dir = Path(body.carpeta) if body.carpeta else SNAPSHOT_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"finanzas_dev_{ts}.db"
    dest = dest_dir / nombre
    shutil.copy2(settings.db_path, dest)
    tamano_kb = round(dest.stat().st_size / 1024, 1)
    return {"ok": True, "nombre_archivo": nombre, "ruta": str(dest), "tamano_kb": tamano_kb}


# ---------------------------------------------------------------------------
# GET /tools/snapshots
# ---------------------------------------------------------------------------

@router.get("/snapshots")
async def listar_snapshots():
    """Lista snapshots disponibles ordenados por fecha descendente."""
    _guard_dev()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    archivos = sorted(SNAPSHOT_DIR.glob("*.db"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "items": [
            {
                "nombre": f.name,
                "tamano_kb": round(f.stat().st_size / 1024, 1),
                "creado_en": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for f in archivos
        ]
    }


# ---------------------------------------------------------------------------
# POST /tools/restore
# ---------------------------------------------------------------------------

class RestoreRequest(BaseModel):
    nombre_archivo: str


@router.post("/restore")
async def restore(body: RestoreRequest):
    """Restaura la DB desde un snapshot. Cierra el pool antes de copiar."""
    _guard_dev()
    # Prevenir path traversal
    nombre = Path(body.nombre_archivo).name
    if nombre != body.nombre_archivo or not nombre.endswith(".db"):
        raise HTTPException(status_code=422, detail="nombre_archivo invalido")
    origen = SNAPSHOT_DIR / nombre
    if not origen.exists():
        raise HTTPException(status_code=404, detail=f"Snapshot '{nombre}' no encontrado")
    # Cerrar pool para liberar el archivo, luego copiar
    await engine.dispose()
    shutil.copy2(origen, settings.db_path)
    return {"ok": True, "restaurado_desde": nombre}


# ---------------------------------------------------------------------------
# GET /tools/log-ejecuciones
# ---------------------------------------------------------------------------

@router.get("/log-ejecuciones")
async def log_ejecuciones(
    desde: str = "",
    hasta: str = "",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    _guard_dev()
    q = "SELECT * FROM log_ejecuciones WHERE 1=1"
    params: dict = {}
    if desde:
        q += " AND fecha_inicio >= :desde"
        params["desde"] = desde
    if hasta:
        q += " AND fecha_inicio <= :hasta"
        params["hasta"] = hasta + "T23:59:59"
    q += " ORDER BY fecha_inicio DESC LIMIT :limit"
    params["limit"] = limit
    rows = (await db.execute(text(q), params)).mappings().all()
    items = []
    for r in rows:
        row = dict(r)
        try:
            row["alertas"] = json.loads(row.get("alertas") or "{}")
        except (json.JSONDecodeError, TypeError):
            row["alertas"] = {}
        items.append(row)
    return {"items": items}


# ---------------------------------------------------------------------------
# POST /tools/seed
# ---------------------------------------------------------------------------

class SeedRequest(BaseModel):
    prefijo: str = "SEED"
    fecha_base: str = ""   # ISO date YYYY-MM-DD; default = hoy


@router.post("/seed", status_code=201)
async def seed(body: SeedRequest = SeedRequest(), db: AsyncSession = Depends(get_db)):
    """
    Inserta 4 transacciones de prueba que cubren los casos de test del ETL.
    Los IDs llevan timestamp para evitar colisiones entre corridas.
    """
    _guard_dev()
    p = body.prefijo
    ts = int(time.time())

    if body.fecha_base:
        base = datetime.fromisoformat(body.fecha_base)
    else:
        base = datetime.now()

    def fstr(d: datetime) -> str:
        return d.strftime("%Y-%m-%d")

    now_iso = datetime.now(timezone.utc).isoformat()

    # --- TX-001: solo notificacion (estado_enriquecimiento='inicial') ------
    id1 = f"{p}-001-{ts}"
    db.add(Transaccion(
        id=id1,
        fecha=fstr(base - timedelta(days=3)),
        tipo="gasto",
        descripcion=f"[{p}] Notificacion Nequi - GHR",
        estado="pendiente",
        confianza=0.4,
        revisado_humano=0,
        completitud="minimo",
        origen="email",
        quien_pago="GHR",
        estado_enriquecimiento="inicial",
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Tramo(
        id_transaccion=id1,
        numero_orden=1,
        monto_origen=85000,
        moneda_origen="COP",
        estado="pendiente",
    ))

    # --- TX-002: enriquecido con vinculo tipo factura ----------------------
    id2 = f"{p}-002-{ts}"
    doc2_id = f"{p}-DOC-002-{ts}"
    db.add(Transaccion(
        id=id2,
        fecha=fstr(base - timedelta(days=2)),
        tipo="gasto",
        descripcion=f"[{p}] Compra Exito - GHR",
        estado="pendiente",
        confianza=0.75,
        revisado_humano=0,
        completitud="minimo",
        origen="email",
        quien_pago="GHR",
        estado_enriquecimiento="enriquecido",
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Tramo(
        id_transaccion=id2,
        numero_orden=1,
        monto_origen=234500,
        moneda_origen="COP",
        estado="pendiente",
    ))
    db.add(Documento(
        id=doc2_id,
        nombre_archivo="factura_exito.pdf",
        ruta=f"data/dev/docs/{doc2_id}.pdf",
        tipo_mime="application/pdf",
        estado="clasificado",
        procesado=True,
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Vinculo(
        id_documento=doc2_id,
        id_transaccion=id2,
        tipo_vinculo="factura",
        confianza=0.85,
        fecha_vinculo=fstr(base - timedelta(days=2)),
        creado_por="seed",
    ))

    # --- TX-003: completo con vinculo tipo extracto ------------------------
    id3 = f"{p}-003-{ts}"
    doc3_id = f"{p}-DOC-003-{ts}"
    db.add(Transaccion(
        id=id3,
        fecha=fstr(base - timedelta(days=1)),
        tipo="gasto",
        descripcion=f"[{p}] Pago Netflix MC",
        estado="pendiente",
        confianza=0.95,
        revisado_humano=0,
        completitud="minimo",
        origen="email",
        quien_pago="MC",
        estado_enriquecimiento="completo",
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Tramo(
        id_transaccion=id3,
        numero_orden=1,
        monto_origen=17900,
        moneda_origen="COP",
        estado="pendiente",
    ))
    db.add(Documento(
        id=doc3_id,
        nombre_archivo="extracto_bancolombia_jun.pdf",
        ruta=f"data/dev/docs/{doc3_id}.pdf",
        tipo_mime="application/pdf",
        estado="clasificado",
        procesado=True,
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Vinculo(
        id_documento=doc3_id,
        id_transaccion=id3,
        tipo_vinculo="extracto",
        confianza=0.90,
        fecha_vinculo=fstr(base - timedelta(days=1)),
        creado_por="seed",
    ))

    # --- TX-004: entidad potencial pendiente (activa PEN-004) --------------
    id4 = f"{p}-004-{ts}"
    db.add(Transaccion(
        id=id4,
        fecha=fstr(base),
        tipo="gasto",
        descripcion=f"[{p}] Pago Ferreteria Los Pinos - GHR",
        estado="pendiente",
        confianza=0.6,
        revisado_humano=0,
        completitud="minimo",
        origen="email",
        quien_pago="GHR",
        estado_enriquecimiento="inicial",
        creado_en=datetime.now(timezone.utc),
    ))
    db.add(Tramo(
        id_transaccion=id4,
        numero_orden=1,
        monto_origen=45000,
        moneda_origen="COP",
        estado="pendiente",
    ))
    db.add(EntidadPotencial(
        tipo="contraparte",
        valor_propuesto="FERRETERIA LOS PINOS",
        id_transaccion=id4,
        estado="pendiente",
        creado_en=now_iso,
    ))

    await db.commit()
    return {
        "ok": True,
        "ids": [id1, id2, id3, id4],
        "prefijo": p,
        "fecha_base": fstr(base),
    }
