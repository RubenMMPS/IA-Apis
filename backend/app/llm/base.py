from abc import ABC, abstractmethod
from app.llm.models import LLMRequest, LLMResponse

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        ...