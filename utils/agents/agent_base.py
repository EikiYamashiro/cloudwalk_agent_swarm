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
    
class AgentBase:
    
    def __init__(self, tools, system_prompt):
        self.llm = llm
        self.tools = tools
        self.agent_executor = create_agent(llm, tools)
        self.system_prompt = system_prompt
        
    def invoke(self, state: State):
        last_message = state["messages"][-1]

        messages = [
            {"role": "system",
            "content": self.system_prompt
            },
            {
                "role": "user",
                "content": last_message.content
            }
        ]
        reply = self.agent_executor.invoke({"messages": messages})
        return {"messages": [{"role": "assistant", "content": reply["messages"][-1].content}]}

