from pydantic import BaseModel
from typing import Literal, Optional

class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    # tools will be added later

class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: LLMUsage
    finish_reason: str