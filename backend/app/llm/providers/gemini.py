from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse, LLMUsage, ToolDefinition, ToolCall
from app.llm.exceptions import LLMProviderError, LLMResponseParsingError

_TYPE_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
}


def _build_gemini_tools(tools: list[ToolDefinition]) -> list[types.Tool] | None:
    if not tools:
        return None
    declarations = [
        types.FunctionDeclaration(
            name=t.name,
            description=t.description,
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    p.name: types.Schema(type=_TYPE_MAP[p.type], description=p.description)
                    for p in t.parameters
                },
                required=[p.name for p in t.parameters if p.required],
            ),
        )
        for t in tools
    ]
    return [types.Tool(function_declarations=declarations)]


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
                    tools=_build_gemini_tools(request.tools),
                ),
            )
        except APIError as e:
            raise LLMProviderError(f"Error del proveedor Gemini: {e}") from e

        try:
            candidate = response.candidates[0]
            tool_calls = []
            text_parts = []

            for part in candidate.content.parts:
                if part.function_call:
                    tool_calls.append(ToolCall(
                        id=part.function_call.name,  # Gemini no da un id propio; usamos el nombre
                        name=part.function_call.name,
                        arguments=dict(part.function_call.args),
                    ))
                elif part.text:
                    text_parts.append(part.text)

            return LLMResponse(
                content="".join(text_parts),
                model=self._model_name,
                usage=LLMUsage(
                    prompt_tokens=response.usage_metadata.prompt_token_count,
                    completion_tokens=response.usage_metadata.candidates_token_count,
                    total_tokens=response.usage_metadata.total_token_count,
                ),
                finish_reason=str(candidate.finish_reason),
                tool_calls=tool_calls,
            )
        except (IndexError, AttributeError) as e:
            raise LLMResponseParsingError(
                f"Respuesta de Gemini con formato inesperado: {e}"
            ) from e