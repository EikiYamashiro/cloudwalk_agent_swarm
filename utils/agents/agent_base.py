from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict
from langchain.agents import create_agent
from utils.factory.llm import get_chat_model

llm = get_chat_model()

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    next: str | None
    user_id: str | None
    username: str | None
    safety_decision: str | None
    safety_category: str | None
    blocked_reason: str | None
    
class AgentBase:
    
    def __init__(self, tools, system_prompt):
        self.llm = llm
        self.tools = tools
        self.agent_executor = create_agent(llm, tools)
        self.system_prompt = system_prompt

    def _build_conversation(self, state: State, limit: int = 8) -> list[dict[str, str]]:
        messages = state.get("messages", [])[-limit:]
        normalized_messages: list[dict[str, str]] = []

        for message in messages:
            role = getattr(message, "type", None)
            content = getattr(message, "content", None)

            if role is None and isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")

            if role is None or content is None:
                continue

            if role in {"human", "user"}:
                normalized_role = "user"
            elif role in {"ai", "assistant"}:
                normalized_role = "assistant"
            elif role == "system":
                normalized_role = "system"
            else:
                continue

            normalized_messages.append(
                {"role": normalized_role, "content": str(content)}
            )

        return normalized_messages
        
    def invoke(self, state: State):
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._build_conversation(state))
        reply = self.agent_executor.invoke({"messages": messages})
        return {"messages": [{"role": "assistant", "content": reply["messages"][-1].content}]}

