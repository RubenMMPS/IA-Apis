import asyncio
from app.core.events import EventBus, TaskEvent


async def _collect_until_finished(bus: EventBus, task_id: str) -> list[TaskEvent]:
    collected = []
    async for event in bus.subscribe(task_id):
        collected.append(event)
    return collected


async def test_publish_subscribe_order():
    bus = EventBus()
    task_id = "t1"

    consumer = asyncio.create_task(_collect_until_finished(bus, task_id))
    await asyncio.sleep(0.05)

    bus.publish(task_id, TaskEvent(event_type="agent_started", agent="planner", message="start"))
    bus.publish(task_id, TaskEvent(event_type="task_completed", message="done"))

    result = await consumer
    assert [e.event_type for e in result] == ["agent_started", "task_completed"]


async def test_queue_closes_after_task_failed():
    bus = EventBus()
    task_id = "t2"

    consumer = asyncio.create_task(_collect_until_finished(bus, task_id))
    await asyncio.sleep(0.05)
    bus.publish(task_id, TaskEvent(event_type="task_failed", message="fail"))

    result = await consumer
    assert len(result) == 1
    assert task_id not in bus._queues  # la cola se limpia tras el evento final