from pydantic import BaseModel
from typing import Literal

class ReviewFeedback(BaseModel):
    decision: Literal["approved", "changes_requested"]
    comments: str