from app.graph.state.graph_state import GraphState
from app.graph.state.test_result import TestResult
from app.graph.state.messages import AgentMessage
from app.graph.state.errors import ErrorRecord
from app.agents.tools.docker_runner import DockerTestRunner
from app.core.events import event_bus, TaskEvent

class TesterAgent:
    name = "tester"

    def __init__(self, runner: DockerTestRunner | None = None):
        self._runner = runner or DockerTestRunner()

    async def run(self, state: GraphState) -> dict:
        task_id = state["task_id"]
        event_bus.publish(task_id, TaskEvent(event_type="agent_started", agent=self.name, message="Tester iniciado"))

        code = state.get("code_artifacts")
        if code is None:
            delta = {
                "errors": [ErrorRecord(agent=self.name, message="No hay code_artifacts que testear", severity="fatal")],
                "current_node": self.name,
            }
            event_bus.publish(task_id, TaskEvent(event_type="agent_error", agent=self.name, message=delta["errors"][0].message))
            return delta

        passed, exit_code, output = await self._runner.run_tests(code.files)
        result = TestResult(passed=passed, exit_code=exit_code, output=output)

        event_bus.publish(task_id, TaskEvent(
            event_type="agent_completed", agent=self.name,
            message=f"Tests {'pasaron' if passed else 'fallaron'} (exit_code={exit_code})",
        ))

        return {
            "test_results": result,
            "messages": [AgentMessage(agent=self.name, content=f"Tests {'pasaron' if passed else 'fallaron'} (exit_code={exit_code})")],
            "current_node": self.name,
        }