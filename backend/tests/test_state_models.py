import pytest
from pydantic import ValidationError
from app.graph.state.messages import AgentMessage
from app.graph.state.errors import ErrorRecord
from app.graph.state.plan import Plan, PlanStep


def test_agent_message_rejects_invalid_agent():
    with pytest.raises(ValidationError):
        AgentMessage(agent="not_a_real_agent", content="test")


def test_agent_message_valid():
    msg = AgentMessage(agent="planner", content="test")
    assert msg.agent == "planner"


def test_error_record_requires_severity():
    with pytest.raises(ValidationError):
        ErrorRecord(agent="developer", message="fail", severity="not_valid")


def test_plan_step_defaults_to_pending():
    step = PlanStep(id="1", description="do something")
    assert step.status == "pending"


def test_plan_with_multiple_steps():
    plan = Plan(steps=[PlanStep(id="1", description="a"), PlanStep(id="2", description="b")])
    assert len(plan.steps) == 2