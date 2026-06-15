"""
Tests unitarios: BackupService
"""

import pytest
from backend.services.backup_service import BackupService


def test_nombre_archivo_formato():
    """El nombre del ZIP debe seguir el patrón mcghr_backup_YYYYMMDD_HHMMSS.zip"""
    svc = BackupService()
    nombre = svc.nombre_archivo()
    assert nombre.startswith("mcghr_backup_")
    assert nombre.endswith(".zip")
    # YYYYMMDD_HHMMSS = 15 chars
    ts_part = nombre.replace("mcghr_backup_", "").replace(".zip", "")
    assert len(ts_part) == 15
    assert "_" in ts_part


def test_listar_backups_carpeta_inexistente(tmp_path, monkeypatch):
    """Si backup_path no existe, listar devuelve lista vacía sin error."""
    from backend.core.config import settings
    monkeypatch.setattr(settings, "backup_path", str(tmp_path / "no_existe"))
    svc = BackupService()
    assert svc.listar_backups() == []
