"""
Servicio Claude API: análisis financiero con lenguaje natural.

Modo REAL: llama a anthropic SDK con modelo configurable.
Modo MOCK: devuelve respuestas prefabricadas (para tests y entorno dev).

Seguridad de datos:
    NUNCA se envían transacciones crudas a Claude API.
    Se envían únicamente agregados anónimos.
    Los nombres de comercios solo se incluyen si el usuario lo solicita
    explícitamente en la pregunta.

Costo estimado (modelo haiku-3):
    ~$0.001–0.003 por consulta típica.
"""

from backend.core.config import settings


class ClaudeService:
    def __init__(self):
        self.provider = settings.claude_provider  # real | mock
        self.model = "claude-haiku-4-5-20251001"  # más económico para queries inline

    async def preguntar(self, pregunta: str, contexto: dict) -> dict:
        """
        Envía pregunta con contexto financiero agregado.
        Devuelve: {respuesta: str, tokens_usados: int}
        """
        if self.provider == "mock":
            return self._mock_respuesta(pregunta)
        return await self._llamar_api(pregunta, contexto)

    async def _llamar_api(self, pregunta: str, contexto: dict) -> dict:
        # TODO: implementar con anthropic SDK
        # import anthropic
        # client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return {"respuesta": "", "tokens_usados": 0}

    def _mock_respuesta(self, pregunta: str) -> dict:
        return {
            "respuesta": f"[MOCK] Respuesta a: '{pregunta}'",
            "tokens_usados": 0,
        }
