import uuid
from app.db.session import AsyncSessionLocal
from app.db.repository import get_task, update_task_status
from app.db.models import TaskStatus
from app.llm.dependencies import get_llm_provider
from app.embeddings.dependencies import get_embedding_provider
from app.graph.build_graph import build_graph
import traceback


async def run_graph_for_task(task_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            return
        await update_task_status(session, task_id, TaskStatus.running)

    app = build_graph(get_llm_provider(), get_embedding_provider())
    config = {"configurable": {"thread_id": str(task_id)}}

    initial_state = {
        "task_id": str(task_id),
        "original_request": task.original_request,
        "status": "running", "current_node": None,
        "plan": None, "research_findings": None, "architecture_spec": None,
        "code_artifacts": None, "test_results": None, "review_feedback": None,
        "developer_last_run_failed": False,
        "iteration_counts": {}, "messages": [], "errors": [], "schema_version": 1,
    }

    async with AsyncSessionLocal() as session:
        try:
            final_state = await app.ainvoke(initial_state, config)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[task_runner] Excepción en task {task_id}:\n{tb}")  # va a la consola de uvicorn
            await update_task_status(
                session, task_id, TaskStatus.failed,
                error_message=f"{type(e).__name__}: {e}" or "Excepción sin mensaje (ver logs de consola)",
            )
            return

        code = final_state.get("code_artifacts")
        test_results = final_state.get("test_results")
        review = final_state.get("review_feedback")

        if review and review.decision == "approved":
            await update_task_status(
                session, task_id, TaskStatus.completed,
                result_summary=code.notes if code else "Completado sin notas.",
            )
        else:
            reasons = []
            if test_results and not test_results.passed:
                reasons.append(f"Tests no superados tras {final_state.get('iteration_counts', {}).get('developer', 0)} intentos.")
            if review and review.decision == "changes_requested":
                reasons.append(f"Reviewer solicitó cambios: {review.comments}")
            if not reasons:
                reasons.append("El workflow no llegó a completarse (posible límite de reintentos).")
            await update_task_status(
                session, task_id, TaskStatus.failed,
                error_message=" | ".join(reasons),
            )