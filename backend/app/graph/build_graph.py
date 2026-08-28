from langgraph.graph import StateGraph, END

from app.graph.state.graph_state import GraphState
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.tester import TesterAgent
from app.llm.base import LLMProvider
from app.embeddings.base import EmbeddingProvider
from app.agents.reviewer import ReviewerAgent

MAX_DEVELOPER_RETRIES = 3


def route_after_developer(state: GraphState) -> str:
    if state.get("developer_last_run_failed"):
        attempts = state.get("iteration_counts", {}).get("developer", 0)
        return "give_up" if attempts >= MAX_DEVELOPER_RETRIES else "retry"
    return "to_tester"


def route_after_tester(state: GraphState) -> str:
    test_results = state.get("test_results")
    if not (test_results and test_results.passed):
        attempts = state.get("iteration_counts", {}).get("developer", 0)
        return "give_up" if attempts >= MAX_DEVELOPER_RETRIES else "retry"
    return "to_reviewer"


def route_after_reviewer(state: GraphState) -> str:
    feedback = state.get("review_feedback")
    if feedback and feedback.decision == "approved":
        return "done"

    attempts = state.get("iteration_counts", {}).get("developer", 0)
    return "give_up" if attempts >= MAX_DEVELOPER_RETRIES else "retry"


def build_graph(llm_provider, embedding_provider, checkpointer):
    graph = StateGraph(GraphState)

    planner = PlannerAgent(llm_provider)
    researcher = ResearcherAgent(llm_provider, embedding_provider)
    architect = ArchitectAgent(llm_provider)
    developer = DeveloperAgent(llm_provider)
    tester = TesterAgent()
    reviewer = ReviewerAgent(llm_provider)

    graph.add_node("planner", planner.run)
    graph.add_node("researcher", researcher.run)
    graph.add_node("architect", architect.run)
    graph.add_node("developer", developer.run)
    graph.add_node("tester", tester.run)
    graph.add_node("reviewer", reviewer.run)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "architect")
    graph.add_edge("architect", "developer")

    graph.add_conditional_edges(
        "developer", route_after_developer,
        {"retry": "developer", "give_up": END, "to_tester": "tester"},
    )
    graph.add_conditional_edges(
        "tester", route_after_tester,
        {"retry": "developer", "give_up": END, "to_reviewer": "reviewer"},
    )
    graph.add_conditional_edges(
        "reviewer", route_after_reviewer,
        {"retry": "developer", "give_up": END, "done": END},
    )

    return graph.compile(checkpointer=checkpointer)