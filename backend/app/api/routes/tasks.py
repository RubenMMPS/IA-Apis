import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.repository import create_task, get_task
from app.core.task_executor import InProcessExecutor
from app.api.schemas import CreateTaskRequest, TaskResponse
import json
from fastapi.responses import StreamingResponse
from app.core.events import event_bus

router = APIRouter(prefix="/tasks", tags=["tasks"])

async def _sse_generator(task_id: str):
    async for event in event_bus.subscribe(task_id):
        payload = event.model_dump_json()
        yield f"event: {event.event_type}\ndata: {payload}\n\n"


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task_endpoint(
    body: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    task = await create_task(session, body.original_request)

    executor = InProcessExecutor(background_tasks)
    executor.submit(task.id)

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    task = await get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task no encontrada")
    return TaskResponse.model_validate(task)

@router.get("/{task_id}/events")
async def stream_task_events(task_id: uuid.UUID):
    return StreamingResponse(
        _sse_generator(str(task_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )