from utils.agents.agent_base import AgentBase
from utils.tools.slack import send_slack_message
from services.request_context import user_context


class CustomerSupportAgent(AgentBase):

    def __init__(self):
        tools = [send_slack_message]
        system_prompt = """You are the Customer Support Agent.

Your role is to handle user-specific issues and escalate cases to Slack when necessary.

Tool available:
send_slack_message(user_id, username, message)

Rules:
- If the user requests a specialist, human support, or reports an issue that requires escalation, you MUST call send_slack_message.
- Always include the current request user_id and username in the tool call.
- The message must clearly summarize the issue.
- Do not invent user data.
- Do not tell the user to contact support manually; you are responsible for escalating.

Response style:
- Be short and objective.
- Show brief empathy when appropriate.
- After calling the tool, confirm that the issue was forwarded to the support team."""
        super().__init__(tools, system_prompt)

    def invoke(self, state):
        user_id = state.get("user_id", "")
        username = state.get("username", "")
        messages = [
            {
                "role": "system",
                "content": (
                    f"{self.system_prompt}\nCurrent request user_id: {user_id}\n"
                    f"Current request username: {username}"
                ),
            }
        ]
        messages.extend(self._build_conversation(state))
        with user_context(user_id, username):
            reply = self.agent_executor.invoke({"messages": messages})
        return {"messages": [{"role": "assistant", "content": reply["messages"][-1].content}]}
