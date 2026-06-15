"""
Test e2e: flujo completo de confirmación de una transacción desde inbox.

1. Simula ETL escribiendo ítem en inbox_mobile con estado=pendiente
2. Llama GET /inbox → verifica que aparece
3. Llama PATCH /inbox/{id} → edita categoría
4. Llama POST /inbox/{id}/confirmar → confirma
5. Verifica GET /transacciones → la transacción aparece confirmada
6. Verifica GET /inbox → el ítem ya no está pendiente

TODO: implementar cuando los servicios inbox y transacciones estén completos.
"""

import pytest


@pytest.mark.asyncio
async def test_flujo_confirmacion_placeholder(client):
    """Placeholder hasta que inbox_service esté implementado."""
    resp = await client.get("/api/v1/inbox")
    assert resp.status_code == 200
