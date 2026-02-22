from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from services.guardrail_service import sanitize_output, validate_input_message
from services.store_service import get_customer_by_user_id
from utils.agents.agent_base import State
from utils.agents.customer_support_agent import CustomerSupportAgent
from utils.agents.knowledge_agent import KnowledgeAgent
from utils.agents.router_agent import RouterAgent
from utils.agents.transfer_agent import TransferAgent

router_agent = RouterAgent()
knowledge_agent = KnowledgeAgent()
customer_support_agent = CustomerSupportAgent()
transfer_agent = TransferAgent()


def _normalize_response_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts).strip()
    if isinstance(content, dict):
        text = content.get("text")
        if text:
            return str(text)
        return str(content)
    return str(content)


def _extract_message_content(message) -> str:
    content = getattr(message, "content", None)
    if content is not None:
        return _normalize_response_content(content)
    if isinstance(message, dict):
        return _normalize_response_content(message.get("content", ""))
    return _normalize_response_content(message)


def safe_response_node(state: State):
    reason = state.get("blocked_reason") or "Blocked by safety policy."
    return {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"I can't process this request ({reason}). "
                    "Please rephrase it and try again."
                ),
            }
        ]
    }


graph_builder = StateGraph(State)

graph_builder.add_node("classifier", router_agent.classify_message)
graph_builder.add_node("safe_response", safe_response_node)
graph_builder.add_node("customer_support", customer_support_agent.invoke)
graph_builder.add_node("knowledge", knowledge_agent.invoke)
graph_builder.add_node("transfer", transfer_agent.invoke)

graph_builder.add_edge(START, "classifier")
graph_builder.add_conditional_edges(
    "classifier",
    lambda state: state.get("next", "knowledge"),
    {
        "safe_response": "safe_response",
        "customer_support": "customer_support",
        "knowledge": "knowledge",
        "transfer": "transfer",
    },
)

graph_builder.add_edge("safe_response", END)
graph_builder.add_edge("customer_support", END)
graph_builder.add_edge("knowledge", END)
graph_builder.add_edge("transfer", END)
graph = graph_builder.compile(checkpointer=MemorySaver())


def get_answer(user_input: str, user_id: str):
    blocked, reason = validate_input_message(user_input)
    if blocked:
        return f"I can't process this request ({reason})"

    customer = get_customer_by_user_id(user_id)
    username = customer["username"] if customer else ""
    state = {
        "messages": [{"role": "user", "content": user_input}],
        "message_type": None,
        "next": None,
        "user_id": user_id,
        "username": username,
        "safety_decision": None,
        "safety_category": None,
        "blocked_reason": None,
    }
    config = {"configurable": {"thread_id": user_id}}
    state = graph.invoke(state, config=config)

    if state.get("messages") and len(state["messages"]) > 0:
        last_message = state["messages"][-1]
        answer = _extract_message_content(last_message)
        return sanitize_output(answer)

    return "Sorry, I couldn't generate a response."
