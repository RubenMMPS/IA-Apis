from app.llm.base import LLMProvider
from app.llm.models import LLMRequest, LLMResponse, LLMUsage
from app.agents.reviewer import ReviewerAgent
from app.graph.state.plan import Plan
from app.graph.state.code import CodeArtifacts, CodeFile
from app.graph.state.test_result import TestResult


class FakeReviewerLLM(LLMProvider):
    def __init__(self, json_content: str):
        self._content = json_content

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=self._content, model="fake",
            usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            finish_reason="stop",
        )


def make_state(constraints: list[str]) -> dict:
    return {
        "task_id": "test-reviewer",
        "plan": Plan(steps=[], constraints=constraints),
        "code_artifacts": CodeArtifacts(
            files=[CodeFile(filename="app/models.py", content="# code")],
            notes="notes",
        ),
        "test_results": TestResult(passed=True, exit_code=0, output="1 passed"),
    }


async def test_no_violations_keeps_llm_decision_approved():
    llm = FakeReviewerLLM('{"decision": "approved", "comments": "ok", "constraints_violated": []}')
    reviewer = ReviewerAgent(llm)

    delta = await reviewer.run(make_state(constraints=["persistencia en memoria"]))

    assert delta["review_feedback"].decision == "approved"
    assert delta["review_feedback"].constraints_violated == []


async def test_violations_force_changes_requested_even_if_llm_said_approved():
    # El LLM "se equivoca" y dice approved a pesar de listar una violación real
    llm = FakeReviewerLLM(
        '{"decision": "approved", "comments": "usa sqlalchemy", '
        '"constraints_violated": ["no utilizar SQLAlchemy"]}'
    )
    reviewer = ReviewerAgent(llm)

    delta = await reviewer.run(make_state(constraints=["no utilizar SQLAlchemy"]))

    assert delta["review_feedback"].decision == "changes_requested"
    assert delta["review_feedback"].constraints_violated == ["no utilizar SQLAlchemy"]


async def test_violations_and_changes_requested_from_llm_stay_consistent():
    llm = FakeReviewerLLM(
        '{"decision": "changes_requested", "comments": "usa sqlalchemy", '
        '"constraints_violated": ["no utilizar SQLAlchemy"]}'
    )
    reviewer = ReviewerAgent(llm)

    delta = await reviewer.run(make_state(constraints=["no utilizar SQLAlchemy"]))

    assert delta["review_feedback"].decision == "changes_requested"


async def test_no_constraints_at_all_does_not_break_review():
    llm = FakeReviewerLLM('{"decision": "approved", "comments": "ok", "constraints_violated": []}')
    reviewer = ReviewerAgent(llm)

    delta = await reviewer.run(make_state(constraints=[]))

    assert delta["review_feedback"].decision == "approved"