import operator
from typing import Annotated, Literal, Optional, TypedDict

from app.graph.state.messages import AgentMessage
from app.graph.state.errors import ErrorRecord
from app.graph.state.plan import Plan
from app.graph.state.research import ResearchFindings
from app.graph.state.architecture import ArchitectureSpec
from app.graph.state.code import CodeArtifacts

TaskStatus = Literal["queued", "running", "completed", "failed", "failed_max_retries"]

class GraphState(TypedDict):
    # Identidad y control
    task_id: str
    original_request: str
    status: TaskStatus
    current_node: Optional[str]

    # Salida de agentes
    plan: Optional[Plan]
    research_findings: Optional[ResearchFindings]
    architecture_spec: Optional[ArchitectureSpec]
    code_artifacts: Optional[CodeArtifacts]

    # Control de flujo
    iteration_counts: dict[str, int]

    # Observabilidad (reducers: se acumulan, no se sobrescriben)
    messages: Annotated[list[AgentMessage], operator.add]
    errors: Annotated[list[ErrorRecord], operator.add]

    schema_version: int