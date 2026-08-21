from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.graph.state.graph_state import GraphState
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.llm.base import LLMProvider
from app.embeddings.base import EmbeddingProvider


def build_graph(llm_provider: LLMProvider, embedding_provider: EmbeddingProvider):
    graph = StateGraph(GraphState)

    planner = PlannerAgent(llm_provider)
    researcher = ResearcherAgent(llm_provider, embedding_provider)

    graph.add_node("planner", planner.run)
    graph.add_node("researcher", researcher.run)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)