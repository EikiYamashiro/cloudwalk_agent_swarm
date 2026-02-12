from utils.agents.agent_base import AgentBase
from utils.tools.transfer import get_last_transfer, transfer


class CustomerSupportAgent(AgentBase):

    def __init__(self):
        tools = [get_last_transfer, transfer]
        system_prompt = """You are the Customer Support Agent.
Your job is to solve user-specific support issues with short, objective and helpful answers.

You have these tools:
1) get_last_transfer(user_id): returns the latest transfer for a user.
2) transfer(user_id, amount, destination): creates a transfer.

Tool usage rules:
- If user asks about their latest/last/recent transfer, call get_last_transfer.
- If user asks to make/send/create a transfer and amount + destination are available, call transfer.
- If amount or destination is missing for a transfer request, ask only for the missing fields.
- Always use the current request user_id when calling tools.
- Do not invent transfer data. Use tool output as source of truth.

Response style:
- Be direct and practical.
- Show brief empathy only when the user reports a problem.
- After tool calls, summarize the result clearly for the user."""
        super().__init__(tools, system_prompt)

    def invoke(self, state):
        user_id = state.get("user_id", "")
        last_message = state["messages"][-1]
        messages = [
            {
                "role": "system",
                "content": f"{self.system_prompt}\nCurrent request user_id: {user_id}",
            },
            {"role": "user", "content": last_message.content},
        ]
        reply = self.agent_executor.invoke({"messages": messages})
        return {"messages": [{"role": "assistant", "content": reply["messages"][-1].content}]}
