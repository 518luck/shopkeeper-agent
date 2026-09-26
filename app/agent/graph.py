from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState

graph_builder = StateGraph(
    state_schema=DataAgentState,
    context_schema=DataAgentContext,
)
