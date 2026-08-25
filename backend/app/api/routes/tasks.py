import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.repository import create_task, get_task
from app.core.task_executor import InProcessExecutor
from app.api.schemas import CreateTaskRequest, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


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