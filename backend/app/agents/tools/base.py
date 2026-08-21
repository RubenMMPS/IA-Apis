from abc import ABC, abstractmethod
from app.llm.models import ToolDefinition

class Tool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        ...