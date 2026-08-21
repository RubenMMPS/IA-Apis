from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Literal

ErrorSeverity = Literal["recoverable", "fatal"]

class ErrorRecord(BaseModel):
    agent: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))