import traceback
import uuid

from app.db.session import AsyncSessionLocal
from app.db.repository import get_task, update_task_status
from app.db.models import TaskStatus
from app.llm.dependencies import get_llm_provider
from app.embeddings.dependencies import get_embedding_provider
from app.graph.build_graph import build_graph
from app.core.events import event_bus, TaskEvent


async def run_graph_for_task(task_id: uuid.UUID, checkpointer) -> None:
    task_id_str = str(task_id)

    async with AsyncSessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            return
        await update_task_status(session, task_id, TaskStatus.running)

    app = build_graph(get_llm_provider(), get_embedding_provider(), checkpointer)
    config = {"configurable": {"thread_id": task_id_str}}

    initial_state = {
        "task_id": task_id_str,
        "original_request": task.original_request,
        "status": "running", "current_node": None,
        "plan": None, "research_findings": None, "architecture_spec": None,
        "code_artifacts": None, "test_results": None, "review_feedback": None,
        "developer_last_run_failed": False,
        "iteration_counts": {}, "messages": [], "errors": [], "schema_version": 1,
        "planner_last_run_failed": False,
        "researcher_last_run_failed": False,
        "architect_last_run_failed": False,
        "developer_last_run_failed": False,
    }

    async with AsyncSessionLocal() as session:
        try:
            async for _ in app.astream(initial_state, config, stream_mode="updates"):
                pass  # los eventos ya se publican dentro de cada agente; aquí solo dejamos avanzar el grafo

            snapshot = await app.aget_state(config)
            final_state = snapshot.values

        except Exception as e:
            tb = traceback.format_exc()
            print(f"[task_runner] Excepción en task {task_id}:\n{tb}")
            error_msg = f"{type(e).__name__}: {e}" or "Excepción sin mensaje (ver logs de consola)"
            await update_task_status(session, task_id, TaskStatus.failed, error_message=error_msg)
            event_bus.publish(task_id_str, TaskEvent(event_type="task_failed", message=error_msg))
            return

        code = final_state.get("code_artifacts")
        test_results = final_state.get("test_results")
        review = final_state.get("review_feedback")

        if review and review.decision == "approved":
            summary = code.notes if code else "Completado sin notas."
            await update_task_status(session, task_id, TaskStatus.completed, result_summary=summary)
            event_bus.publish(task_id_str, TaskEvent(event_type="task_completed", message="Tarea completada y aprobada"))
        else:
            reasons = []
            if test_results and not test_results.passed:
                attempts = final_state.get("iteration_counts", {}).get("developer", 0)
                reasons.append(f"Tests no superados tras {attempts} intentos.")
            if review and review.decision == "changes_requested":
                reasons.append(f"Reviewer solicitó cambios: {review.comments}")
            if not reasons:
                reasons.append("El workflow no llegó a completarse (posible límite de reintentos).")
            error_msg = " | ".join(reasons)
            await update_task_status(session, task_id, TaskStatus.failed, error_message=error_msg)
            event_bus.publish(task_id_str, TaskEvent(event_type="task_failed", message=error_msg))