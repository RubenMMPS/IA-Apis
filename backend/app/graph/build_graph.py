from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from app.graph.state.graph_state import GraphState
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent

def build_graph(llm_provider, embedding_provider):
    graph = StateGraph(GraphState)

    planner = PlannerAgent(llm_provider)
    researcher = ResearcherAgent(llm_provider, embedding_provider)
    architect = ArchitectAgent(llm_provider)
    developer = DeveloperAgent(llm_provider)

    graph.add_node("planner", planner.run)
    graph.add_node("researcher", researcher.run)
    graph.add_node("architect", architect.run)
    graph.add_node("developer", developer.run)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "architect")
    graph.add_edge("architect", "developer")
    graph.add_edge("developer", END)

    return graph.compile(checkpointer=MemorySaver())