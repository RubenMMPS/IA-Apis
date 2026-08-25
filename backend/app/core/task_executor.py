from abc import ABC, abstractmethod
import uuid


class TaskExecutor(ABC):
    @abstractmethod
    def submit(self, task_id: uuid.UUID) -> None:
        ...


class InProcessExecutor(TaskExecutor):
    def __init__(self, background_tasks):
        self._background_tasks = background_tasks

    def submit(self, task_id: uuid.UUID) -> None:
        from app.core.task_runner import run_graph_for_task
        self._background_tasks.add_task(run_graph_for_task, task_id)