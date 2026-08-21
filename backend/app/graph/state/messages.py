from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Literal

AgentName = Literal[
    "planner", "researcher", "architect", "developer", "tester", "reviewer"
]

class AgentMessage(BaseModel):
    agent: AgentName
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))