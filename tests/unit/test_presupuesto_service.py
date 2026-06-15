"""
Tests unitarios: PresupuestoService
Verifica la fórmula de proyección al cierre del mes.
"""

import pytest
from unittest.mock import AsyncMock, patch
from freezegun import freeze_time
from backend.services.presupuesto_service import PresupuestoService


@pytest.mark.asyncio
@freeze_time("2026-01-15")  # día 15 de enero (31 días)
async def test_factor_proyeccion_mitad_de_mes():
    """A mitad de enero el factor debe ser ≈ 2.067 (31/15)."""
    db = AsyncMock()
    service = PresupuestoService(db)
    resultado = await service.obtener_ejecucion_mes(2026, 1)
    factor = resultado["factor_proyeccion"]
    assert abs(factor - (31 / 15)) < 0.01


@pytest.mark.asyncio
@freeze_time("2026-02-28")  # último día de febrero
async def test_factor_proyeccion_fin_de_mes():
    """Al último día el factor debe ser 1.0 (no multiplica)."""
    db = AsyncMock()
    service = PresupuestoService(db)
    resultado = await service.obtener_ejecucion_mes(2026, 2)
    assert resultado["factor_proyeccion"] == 1.0
