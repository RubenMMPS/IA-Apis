import json
from groq import AsyncGroq, GroqError

from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse, LLMUsage, ToolDefinition, ToolCall
from app.llm.exceptions import LLMProviderError, LLMResponseParsingError


def _build_tools_param(tools: list[ToolDefinition]) -> list[dict] | None:
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {"type": p.type, "description": p.description}
                        for p in t.parameters
                    },
                    "required": [p.name for p in t.parameters if p.required],
                },
            },
        }
        for t in tools
    ]


# ...existing code...
class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        self._client = AsyncGroq(api_key=api_key)
        self._model_name = model_name

    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            payload = {
                "model": self._model_name,
                "messages": [
                    {"role": m.role, "content": m.content}
                    for m in request.messages
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            tools_param = _build_tools_param(request.tools)
            if tools_param:
                payload["tools"] = tools_param
                payload["tool_choice"] = "auto"  # importante para Groq

            completion = await self._client.chat.completions.create(**payload)

        except GroqError as e:
            raise LLMProviderError(f"Error del proveedor Groq: {e}") from e

        try:
            choice = completion.choices[0]

            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in (choice.message.tool_calls or [])
            ]

            return LLMResponse(
                content=choice.message.content or "",
                model=completion.model,
                usage=LLMUsage(
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                ),
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
            )
        except (IndexError, AttributeError) as e:
            raise LLMResponseParsingError(
                f"Respuesta de Groq con formato inesperado: {e}"
            ) from e