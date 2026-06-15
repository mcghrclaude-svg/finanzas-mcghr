"""
Router: /api/v1/backup
Backup completo y restauración del sistema.

Estrategia:
    - Siempre completo (nunca incremental por diseño)
    - Contenido del ZIP:
        ├── finanzas.db            SQLite completo
        ├── config/               config_correos.json, .env.prod
        ├── oauth_tokens/         tokens cifrados (AES-256 en Fase 2)
        ├── documentos/           todos los PDFs vinculados
        ├── reglas/               reglas_clasificacion.json
        └── restore.py            script autosuficiente de restauración
    - Retención: 90 días, rotación automática
    - Destino: backup_path configurado en Settings (puede ser OneDrive)
    - restore.py es ejecutable standalone: no requiere que el servidor esté corriendo

Nomenclatura: mcghr_backup_YYYYMMDD_HHMMSS.zip
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.post("/crear", status_code=202)
async def crear_backup(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia creación del backup en background.
    Devuelve job_id para consultar el estado.
    El ZIP se escribe en backup_path de Settings.
    """
    # TODO: background_tasks.add_task(backup_service.crear_backup)
    return {"job_id": None, "estado": "iniciado", "estimado_segundos": 30}


@router.get("/estado/{job_id}")
async def estado_backup(job_id: str):
    """
    Consulta el progreso del backup. Polling desde el frontend.
    Estados: iniciado | en_progreso | completado | error
    """
    return {"job_id": job_id, "estado": "completado", "ruta": None, "tamano_mb": 0}


@router.get("/historial")
async def historial_backups():
    """
    Lista los backups disponibles en backup_path con fecha y tamaño.
    Filtra automáticamente los que superan 90 días.
    """
    return {"items": []}


@router.get("/descargar/{nombre_archivo}")
async def descargar_backup(nombre_archivo: str):
    """
    Descarga el ZIP de backup. Solo archivos en backup_path —
    nunca rutas absolutas externas (prevención de path traversal).
    """
    # TODO: validar que nombre_archivo no contenga ../
    return FileResponse(path="/placeholder", filename=nombre_archivo)


@router.post("/restaurar", status_code=202)
async def restaurar_backup(
    background_tasks: BackgroundTasks,
):
    """
    Restaura desde un ZIP subido o desde un archivo en backup_path.
    Body: { fuente: 'upload' | 'archivo', nombre_archivo: str }
    
    ADVERTENCIA: reemplaza la base de datos completa.
    El frontend debe pedir confirmación explícita antes de llamar este endpoint.
    """
    # TODO: background_tasks.add_task(backup_service.restaurar, ...)
    return {"job_id": None, "estado": "iniciado"}


@router.delete("/limpiar-antiguos", status_code=204)
async def limpiar_backups_antiguos():
    """
    Elimina backups con más de 90 días. Ejecutado automáticamente
    tras cada backup exitoso; también disponible manualmente.
    """
    return None
