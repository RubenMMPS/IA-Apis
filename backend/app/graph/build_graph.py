from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.graph.state.graph_state import GraphState
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.tester import TesterAgent
from app.llm.base import LLMProvider
from app.embeddings.base import EmbeddingProvider

MAX_DEVELOPER_RETRIES = 3


def route_after_tester(state: GraphState) -> str:
    test_results = state.get("test_results")
    if test_results and test_results.passed:
        return "done"

    attempts = state.get("iteration_counts", {}).get("developer", 0)
    if attempts >= MAX_DEVELOPER_RETRIES:
        return "give_up"

    return "retry"


def build_graph(llm_provider: LLMProvider, embedding_provider: EmbeddingProvider):
    graph = StateGraph(GraphState)

    planner = PlannerAgent(llm_provider)
    researcher = ResearcherAgent(llm_provider, embedding_provider)
    architect = ArchitectAgent(llm_provider)
    developer = DeveloperAgent(llm_provider)
    tester = TesterAgent()

    graph.add_node("planner", planner.run)
    graph.add_node("researcher", researcher.run)
    graph.add_node("architect", architect.run)
    graph.add_node("developer", developer.run)
    graph.add_node("tester", tester.run)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "architect")
    graph.add_edge("architect", "developer")
    graph.add_edge("developer", "tester")

    graph.add_conditional_edges(
        "tester",
        route_after_tester,
        {
            "retry": "developer",
            "give_up": END,
            "done": END,
        },
    )

    return graph.compile(checkpointer=MemorySaver())