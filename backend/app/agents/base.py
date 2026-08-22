import json
import re
from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel, ValidationError

from app.graph.state.graph_state import GraphState
from app.graph.state.messages import AgentMessage, AgentName
from app.graph.state.errors import ErrorRecord
from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMMessage, ToolDefinition, ToolCall
from app.llm.exceptions import LLMProviderError

MAX_PARSE_RETRIES = 2


class AgentOutputParsingError(Exception):
    pass


def _normalize_json_text(text: str) -> str:
    """Extrae JSON de texto que puede venir envuelto en markdown/bloques de código."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


class BaseAgent(ABC):
    name: AgentName
    tools: list[ToolDefinition] = []
    tool_registry: dict[str, "Tool"] = {}
    max_tool_iterations: int = 5
    max_output_tokens: int = 2048

    def __init__(self, llm: LLMProvider):
        self._llm = llm
        self.tools = list(self.tools)
        self.tool_registry = dict(self.tool_registry)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def build_user_message(self, state: GraphState) -> str:
        ...

    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        ...

    @abstractmethod
    def apply_output(self, state: GraphState, output: BaseModel) -> dict:
        ...

    def _compact_schema_hint(self) -> str:
        schema = self.output_schema().model_json_schema()
        defs = schema.get("$defs", {})

        def describe(props: dict) -> str:
            lines = []
            for name, info in props.items():
                type_hint = info.get("type", "object")
                if "$ref" in info:
                    ref_name = info["$ref"].split("/")[-1]
                    nested = defs.get(ref_name, {}).get("properties", {})
                    type_hint = "{" + ", ".join(nested.keys()) + "}"
                elif info.get("type") == "array":
                    items = info.get("items", {})
                    if "$ref" in items:
                        ref_name = items["$ref"].split("/")[-1]
                        nested = defs.get(ref_name, {}).get("properties", {})
                        type_hint = "list of {" + ", ".join(nested.keys()) + "}"
                    else:
                        type_hint = f"list of {items.get('type', 'string')}"
                lines.append(f'  "{name}": {type_hint}')
            return "{\n" + ",\n".join(lines) + "\n}"

        return describe(schema.get("properties", {}))

    def _full_system_prompt(self) -> str:
        schema_hint = self._compact_schema_hint()
        return (
            f"{self.system_prompt}\n\n"
            "Debes responder ÚNICAMENTE con un JSON válido que cumpla esta forma "
            f"(sin texto adicional, sin backticks):\n{schema_hint}"
        )

    async def run(self, state: GraphState) -> dict:
        messages = [
            LLMMessage(role="system", content=self._full_system_prompt()),
            LLMMessage(role="user", content=self.build_user_message(state)),
        ]

        try:
            output = await self._generate_with_retries(messages)
        except LLMProviderError as e:
            return self._error_delta(f"Fallo del proveedor LLM: {e}", "recoverable")
        except AgentOutputParsingError as e:
            return self._error_delta(f"Salida inválida tras reintentos: {e}", "fatal")

        delta = self.apply_output(state, output)
        delta["messages"] = [AgentMessage(agent=self.name, content=f"{self.name} completó su tarea")]
        delta["current_node"] = self.name
        return delta

    async def _generate_with_retries(self, messages: list[LLMMessage]) -> BaseModel:
        schema = self.output_schema()
        conversation = list(messages)
        last_error: Exception | None = None
        tool_used = False

        for _ in range(self.max_tool_iterations):
            active_tools = [] if tool_used else self.tools
            response = await self._llm.generate(
                LLMRequest(messages=conversation, tools=active_tools, max_tokens=self.max_output_tokens)
            )

            if response.tool_calls:
                tool_used = True
                conversation.append(LLMMessage(role="assistant", content=response.content or ""))
                for call in response.tool_calls:
                    result = await self._execute_tool(call)
                    conversation.append(LLMMessage(
                        role="user",
                        content=f"Resultado de la tool '{call.name}': {result}",
                    ))
                continue

            try:
                clean = _normalize_json_text(response.content)
                return schema.model_validate_json(clean)
            except (ValidationError, ValueError) as e:
                last_error = e
                conversation.append(LLMMessage(role="assistant", content=response.content))
                conversation.append(LLMMessage(
                    role="user",
                    content=f"Tu respuesta no era JSON válido: {e}. Corrígela, responde solo JSON.",
                ))

        raise AgentOutputParsingError(str(last_error) if last_error else "Límite de iteraciones agotado")

    async def _execute_tool(self, call: ToolCall) -> str:
        tool = self.tool_registry.get(call.name)
        if tool is None:
            return f"Error: tool '{call.name}' no encontrada"
        try:
            return await tool.execute(**call.arguments)
        except Exception as e:
            return f"Error ejecutando la tool: {e}"

    def _error_delta(self, message: str, severity: str) -> dict:
        return {
            "errors": [ErrorRecord(agent=self.name, message=message, severity=severity)],
            "messages": [AgentMessage(agent=self.name, content=f"Error: {message}")],
            "current_node": self.name,
        }