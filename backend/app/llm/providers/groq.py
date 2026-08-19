from groq import AsyncGroq, GroqError

from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse, LLMUsage
from app.llm.exceptions import LLMProviderError, LLMResponseParsingError


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        self._client = AsyncGroq(api_key=api_key)
        self._model_name = model_name

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": m.role, "content": m.content}
                    for m in request.messages
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except GroqError as e:
            raise LLMProviderError(f"Error del proveedor Groq: {e}") from e

        try:
            choice = completion.choices[0]
            return LLMResponse(
                content=choice.message.content,
                model=completion.model,
                usage=LLMUsage(
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                ),
                finish_reason=choice.finish_reason,
            )
        except (IndexError, AttributeError) as e:
            raise LLMResponseParsingError(
                f"Respuesta de Groq con formato inesperado: {e}"
            ) from e