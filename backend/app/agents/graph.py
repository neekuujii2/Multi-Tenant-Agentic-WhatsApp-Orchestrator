"""
LangGraph workflow assembly.
Connects the 4 nodes in a sequential pipeline:
acknowledge -> context_retriever -> llm_reasoning -> dispatcher
"""
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes.acknowledge import acknowledge_node
from app.agents.nodes.context_retriever import context_retriever_node
from app.agents.nodes.llm_reasoning import llm_reasoning_node
from app.agents.nodes.dispatcher import dispatcher_node
from app.utils.logger import get_logger

log = get_logger(__name__)

# Assemble StateGraph
builder = StateGraph(AgentState)

builder.add_node("acknowledge", acknowledge_node)
builder.add_node("context_retriever", context_retriever_node)
builder.add_node("llm_reasoning", llm_reasoning_node)
builder.add_node("dispatcher", dispatcher_node)

builder.set_entry_point("acknowledge")
builder.add_edge("acknowledge", "context_retriever")
builder.add_edge("context_retriever", "llm_reasoning")
builder.add_edge("llm_reasoning", "dispatcher")
builder.add_edge("dispatcher", END)

# Compile graph
graph = builder.compile()


async def run_agent_workflow(initial_state: AgentState) -> dict:
    """
    Executes the LangGraph agent workflow with the given initial state.
    Handles expected interrupts (like human handoff) and unexpected errors.
    """
    try:
        final_state = await graph.ainvoke(initial_state)
        return {
            "status": "success",
            "session_id": final_state.get("session_id"),
            "session_status": final_state.get("session_status"),
            "detected_language": final_state.get("detected_language"),
            "sentiment_score": final_state.get("sentiment_score"),
        }
    except InterruptedError as e:
        log.info(
            "workflow_interrupted",
            tenant_id=initial_state.get("tenant_id"),
            customer_phone=initial_state.get("customer_phone"),
            reason=str(e),
        )
        return {
            "status": "interrupted",
            "reason": str(e),
        }
    except Exception as e:
        log.error(
            "workflow_execution_failed",
            tenant_id=initial_state.get("tenant_id"),
            customer_phone=initial_state.get("customer_phone"),
            error=str(e),
            exc_info=True,
        )
        return {
            "status": "error",
            "reason": str(e),
        }
