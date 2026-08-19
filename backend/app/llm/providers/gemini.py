from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse, LLMUsage
from app.llm.exceptions import LLMProviderError, LLMResponseParsingError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def generate(self, request: LLMRequest) -> LLMResponse:
        system_messages = [m.content for m in request.messages if m.role == "system"]
        conversation = [m for m in request.messages if m.role != "system"]

        contents = [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part.from_text(m.content)],
            )
            for m in conversation
        ]

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction="\n".join(system_messages) or None,
                    temperature=request.temperature,
                    max_output_tokens=request.max_tokens,
                ),
            )
        except APIError as e:
            raise LLMProviderError(f"Error del proveedor Gemini: {e}") from e

        try:
            return LLMResponse(
                content=response.text,
                model=self._model_name,
                usage=LLMUsage(
                    prompt_tokens=response.usage_metadata.prompt_token_count,
                    completion_tokens=response.usage_metadata.candidates_token_count,
                    total_tokens=response.usage_metadata.total_token_count,
                ),
                finish_reason=str(response.candidates[0].finish_reason),
            )
        except (IndexError, AttributeError) as e:
            raise LLMResponseParsingError(
                f"Respuesta de Gemini con formato inesperado: {e}"
            ) from e