import asyncio
import uuid
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel

EventType = Literal[
    "agent_started", "agent_completed", "agent_error",
    "tool_used", "retry", "task_completed", "task_failed",
]


class TaskEvent(BaseModel):
    event_type: EventType
    agent: str | None = None
    message: str
    timestamp: datetime = None

    def model_post_init(self, __context) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class EventBus:
    def __init__(self):
        self._queues: dict[str, asyncio.Queue[TaskEvent]] = {}

    def _get_queue(self, task_id: str) -> asyncio.Queue:
        if task_id not in self._queues:
            self._queues[task_id] = asyncio.Queue()
        return self._queues[task_id]

    def publish(self, task_id: str, event: TaskEvent) -> None:
        self._get_queue(task_id).put_nowait(event)

    async def subscribe(self, task_id: str):
        queue = self._get_queue(task_id)
        while True:
            event = await queue.get()
            yield event
            if event.event_type in ("task_completed", "task_failed"):
                del self._queues[task_id]
                break


event_bus = EventBus()