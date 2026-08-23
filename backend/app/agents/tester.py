from app.graph.state.graph_state import GraphState
from app.graph.state.test_result import TestResult
from app.graph.state.messages import AgentMessage
from app.graph.state.errors import ErrorRecord
from app.agents.tools.docker_runner import DockerTestRunner


class TesterAgent:
    name = "tester"

    def __init__(self, runner: DockerTestRunner | None = None):
        self._runner = runner or DockerTestRunner()

    async def run(self, state: GraphState) -> dict:
        code = state.get("code_artifacts")
        if code is None:
            return {
                "errors": [ErrorRecord(agent=self.name, message="No hay code_artifacts que testear", severity="fatal")],
                "current_node": self.name,
            }

        passed, exit_code, output = await self._runner.run_tests(code.files)

        result = TestResult(passed=passed, exit_code=exit_code, output=output)

        return {
            "test_results": result,
            "messages": [AgentMessage(
                agent=self.name,
                content=f"Tests {'pasaron' if passed else 'fallaron'} (exit_code={exit_code})",
            )],
            "current_node": self.name,
        }