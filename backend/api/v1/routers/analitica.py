"""
Router: /api/v1/analitica
Interacción con Claude API para análisis financiero conversacional.

Fase 1: endpoints que responden preguntas puntuales sobre los datos.
Fase 2: chat conversacional con historial de contexto.
Fase 3: insights embebidos proactivos en el Dashboard.

Seguridad: NUNCA se envían datos brutos de transacciones a Claude API.
Se envían agregados anónimos: totales, porcentajes, promedios.
Los detalles identificatorios (comercio, descripción) se envían solo
cuando el usuario lo solicita explícitamente.

Costo estimado: modelo Haiku a ~$0.25/M tokens → $0.001–0.003 por consulta.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db

router = APIRouter()


@router.post("/consulta")
async def consulta_libre(
    db: AsyncSession = Depends(get_db),
):
    """
    Pregunta en lenguaje natural sobre las finanzas del hogar.
    Body: { pregunta: str, contexto_meses: int = 3 }

    Flujo:
        1. Extrae agregados del período de SQLite
        2. Construye prompt con los datos (sin PII)
        3. Llama a Claude API (via claude_service)
        4. Devuelve respuesta + datos usados como contexto

    Ejemplos de preguntas:
        '¿En qué categoría estamos gastando más que el mes pasado?'
        '¿Cómo reduzco gastos de restaurantes un 20%?'
        '¿Cuánto hemos ahorrado en los últimos 6 meses?'
    """
    # TODO: implementar claude_service.preguntar(pregunta, contexto)
    return {"respuesta": "", "tokens_usados": 0, "contexto_enviado": {}}


@router.get("/resumen-mes")
async def resumen_mes_con_claude(
    anio: int = ...,
    mes: int = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Genera un resumen narrativo del mes con Claude.
    Se embebe en la sección de cierre mensual del Dashboard.
    Cacheado en memoria por sesión (no persiste en DB).
    """
    return {"resumen": "", "generado_en": None}


@router.get("/alertas-inteligentes")
async def alertas_inteligentes(
    db: AsyncSession = Depends(get_db),
):
    """
    Detecta patrones anómalos con Claude:
    - Categorías con desviación > 2σ respecto al promedio histórico
    - Suscripciones que aumentaron de precio
    - Meses con ahorro negativo consecutivos
    Fase 2 — stub para definir contrato de respuesta.
    """
    return {"alertas": []}
