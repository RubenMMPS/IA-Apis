from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse
from app.llm.exceptions import LLMProviderError


class FallbackLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self._primary = primary
        self._secondary = secondary

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            return await self._primary.generate(request)
        except LLMProviderError as primary_error:
            if not primary_error.retryable:
                raise
            try:
                return await self._secondary.generate(request)
            except LLMProviderError as secondary_error:
                raise LLMProviderError(
                    f"Ambos proveedores fallaron. Primario: {primary_error}. "
                    f"Secundario: {secondary_error}",
                    retryable=False,
                ) from secondary_error