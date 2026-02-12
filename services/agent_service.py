from langgraph.graph import StateGraph, START, END
from utils.agents.agent_base import State
from utils.agents.customer_support_agent import CustomerSupportAgent
from utils.agents.router_agent import RouterAgent
from utils.agents.knowledge_agent import KnowledgeAgent

router_agent = RouterAgent()
knowledge_agent = KnowledgeAgent()
customer_support_agent = CustomerSupportAgent()

graph_builder = StateGraph(State)

graph_builder.add_node("classifier", router_agent.classify_message)
graph_builder.add_node("router", router_agent.router)
graph_builder.add_node("customer_support", customer_support_agent.invoke)
graph_builder.add_node("knowledge", knowledge_agent.invoke)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges("router", 
                                    lambda state: state["next"],
                                    {
                                        "customer_support": "customer_support",
                                        "knowledge": "knowledge"
                                    })

graph_builder.add_edge("customer_support", END)
graph_builder.add_edge("knowledge", END)
graph = graph_builder.compile()

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

def get_answer(user_input: str, user_id: str):
    state = {"messages": [], "message_type": None, "user_id": user_id}
    state["messages"] = state.get("messages", []) + [{"role": "user", "content": user_input}]
    state = graph.invoke(state)

    if state.get("messages") and len(state["messages"]) > 0:
        last_message = state["messages"][-1]
        return _normalize_response_content(last_message.content)

    return "Sorry, I couldn't generate a response."
