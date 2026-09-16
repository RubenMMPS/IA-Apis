import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from langgraph.checkpoint.memory import MemorySaver
from app.llm.dependencies import get_llm_provider
from app.embeddings.dependencies import get_embedding_provider
from app.graph.build_graph import build_graph
from evals.judge import judge_code

GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.json"
RESULTS_DIR = Path(__file__).parent / "results"


def make_initial_state(task_id: str, request: str) -> dict:
    return {
        "task_id": task_id, "original_request": request,
        "status": "running", "current_node": None,
        "plan": None, "research_findings": None, "architecture_spec": None,
        "code_artifacts": None, "test_results": None, "review_feedback": None,
        "planner_last_run_failed": False, "researcher_last_run_failed": False,
        "architect_last_run_failed": False, "developer_last_run_failed": False,
        "iteration_counts": {}, "messages": [], "errors": [], "schema_version": 1,
        "token_usage": {},
    }


async def run_single_case(case: dict, llm, embeddings) -> dict:
    app = build_graph(llm, embeddings, MemorySaver())
    config = {"configurable": {"thread_id": f"eval-{case['id']}"}}
    initial_state = make_initial_state(f"eval-{case['id']}", case["request"])

    start = time.monotonic()
    try:
        final_state = await app.ainvoke(initial_state, config)
    except Exception as e:
        return {
            "id": case["id"], "success": False, "error": f"{type(e).__name__}: {e}",
            "duration_seconds": round(time.monotonic() - start, 1),
            "errors_detail": [],
            "judge_score": None,
        }
    duration = time.monotonic() - start

    review = final_state.get("review_feedback")
    test_results = final_state.get("test_results")
    plan = final_state.get("plan")
    code = final_state.get("code_artifacts")
    architecture_spec = final_state.get("architecture_spec")
    usage = final_state.get("token_usage", {})
    errors_detail = [f"[{e.agent}] {e.message[:150]}" for e in final_state.get("errors", [])]

    success = bool(review and review.decision == "approved")
    constraints_detected = bool(plan and plan.constraints) if case.get("constraints_expected") else True

    judge_score = None
    if success and code:
        try:
            score = await judge_code(
                llm, case["request"], architecture_spec, code,
                plan.constraints if plan else [],
            )
            judge_score = score.model_dump()
        except Exception as e:
            judge_score = {"error": f"{type(e).__name__}: {e}"}

    return {
        "id": case["id"],
        "success": success,
        "constraints_expected": bool(case.get("constraints_expected")),
        "constraints_detected": constraints_detected,
        "developer_attempts": final_state.get("iteration_counts", {}).get("developer", 0),
        "tests_passed": bool(test_results and test_results.passed),
        "review_decision": review.decision if review else None,
        "constraints_violated": review.constraints_violated if review else [],
        "total_tokens": usage.get("total_tokens", 0),
        "duration_seconds": round(duration, 1),
        "error": None if success else (final_state.get("errors", [])[-1].message if final_state.get("errors") else "no aprobado"),
        "errors_detail": errors_detail,
        "judge_score": judge_score,
    }


async def main(case_ids: list[str] | None = None):
    cases = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    if case_ids:
        cases = [c for c in cases if c["id"] in case_ids]

    llm = get_llm_provider()
    embeddings = get_embedding_provider()

    results = []
    for case in cases:
        print(f"Ejecutando: {case['id']}...")
        result = await run_single_case(case, llm, embeddings)
        results.append(result)
        print(f"  -> success={result['success']} tokens={result['total_tokens']} duration={result['duration_seconds']}s")
        if result.get("errors_detail"):
            for err in result["errors_detail"]:
                print(f"     ERROR: {err}")
        if result.get("judge_score") and "error" not in result["judge_score"]:
            js = result["judge_score"]
            print(f"     judge: correctness={js['correctness']} readability={js['readability']} "
                  f"plan_adherence={js['plan_adherence']} constraints={js['constraints_compliance']}")

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"eval_{timestamp}.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    total_tokens = sum(r["total_tokens"] for r in results)

    scored = [r["judge_score"] for r in results if r.get("judge_score") and "error" not in r["judge_score"]]

    print(f"\n=== Resumen ===")
    print(f"Tasa de éxito: {passed}/{total} ({100*passed/total:.0f}%)" if total else "Sin casos ejecutados")
    print(f"Tokens totales: {total_tokens}")
    if scored:
        avg_correctness = sum(s["correctness"] for s in scored) / len(scored)
        avg_readability = sum(s["readability"] for s in scored) / len(scored)
        print(f"Correctness media (solo casos evaluados): {avg_correctness:.1f}/5")
        print(f"Readability media (solo casos evaluados): {avg_readability:.1f}/5")
    print(f"Resultados guardados en: {output_path}")


if __name__ == "__main__":
    import sys
    case_ids = sys.argv[1:] if len(sys.argv) > 1 else None
    asyncio.run(main(case_ids))