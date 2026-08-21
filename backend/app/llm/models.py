from pydantic import BaseModel
from typing import Literal, Optional


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ToolParameter(BaseModel):
    name: str
    description: str
    type: Literal["string", "integer", "number", "boolean"]
    required: bool = True


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: list[ToolDefinition] = []


class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: LLMUsage
    finish_reason: str
    tool_calls: list[ToolCall] = []