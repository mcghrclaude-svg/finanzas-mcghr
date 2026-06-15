"""
Servicio de backup: creación y restauración de ZIPs completos.

Contenido del ZIP (siempre completo, nunca incremental):
    finanzas.db
    config/config_correos.json
    config/.env.prod
    oauth_tokens/*.json  (Fase 2: cifrados)
    documentos/**/*.pdf
    reglas/reglas_clasificacion.json
    restore.py           (script autosuficiente)

Retención: 90 días. Rotación automática post-creación exitosa.
"""

import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from backend.core.config import settings


class BackupService:
    RETENTION_DAYS = 90
    RESTORE_SCRIPT = "restore.py"  # incluido en cada ZIP

    def nombre_archivo(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"mcghr_backup_{ts}.zip"

    async def crear_backup(self) -> Path:
        """
        Crea el ZIP completo y devuelve su ruta.
        Llama a limpiar_antiguos() al finalizar.
        TODO: implementar
        """
        ruta = Path(settings.backup_path) / self.nombre_archivo()
        # TODO: armar ZIP con todos los componentes
        return ruta

    async def restaurar(self, ruta_zip: Path) -> bool:
        """
        Extrae el ZIP y reemplaza la DB y configs.
        ADVERTENCIA: operación destructiva — requiere confirmación previa.
        TODO: implementar
        """
        return False

    def listar_backups(self) -> list[dict]:
        carpeta = Path(settings.backup_path)
        if not carpeta.exists():
            return []
        archivos = sorted(carpeta.glob("mcghr_backup_*.zip"), reverse=True)
        return [
            {"nombre": f.name, "tamano_mb": round(f.stat().st_size / 1_048_576, 2), "fecha": f.stat().st_mtime}
            for f in archivos
        ]

    def limpiar_antiguos(self):
        corte = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        carpeta = Path(settings.backup_path)
        for f in carpeta.glob("mcghr_backup_*.zip"):
            if datetime.fromtimestamp(f.stat().st_mtime) < corte:
                f.unlink()
