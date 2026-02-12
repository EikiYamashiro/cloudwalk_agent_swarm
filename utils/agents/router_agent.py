from utils.agents.agent_base import AgentBase, State
from typing import Literal
from pydantic import BaseModel, Field

class MessageClassifier(BaseModel):
    message_type: Literal["knowledge", "customer_support"] = Field(
        ...,
        description="Classify the user's message as either 'knowledge' or 'customer_support'"
    )

class RouterAgent(AgentBase):
    def __init__(self):
        self.system_prompt = """You are the Router Agent.
Classify every user message into exactly one label:
- 'knowledge'
- 'customer_support'

Use 'knowledge' when the user is asking for information, facts, explanations, comparisons, pricing, product features, company services, or general news/current events.
Examples:
- "What are the fees of the Maquininha Smart?"
- "How can I use my phone as a card machine?"
- "Quando foi o ultimo jogo do Palmeiras?"
- "Quais as principais noticias de Sao Paulo hoje?"

Use 'customer_support' when the user has a personal/account/operational issue and needs help resolving a problem.
Examples:
- "Why I am not able to make transfers?"
- "I can't sign in to my account."
- "Meu Pix falhou, o que faco?"
- "Nao consigo acessar minha conta."
- "Faça uma transferência de R$100 para o João da Silva."

If the message is ambiguous, prefer:
- 'customer_support' for user-specific issues, incidents, failures, account access, transfers, payments, or troubleshooting.
- 'knowledge' for informational questions not tied to a specific user account problem.

Return only one of these exact labels: 'knowledge' or 'customer_support'.
"""
        super().__init__([], self.system_prompt)

    def router(self, state: State):
        message_type = state.get("message_type", "knowledge")
        if message_type == "customer_support":
            return {"next": "customer_support"}
        
        return {"next": "knowledge"}

    def classify_message(self, state: State):
        last_message = state["messages"][-1]
        classifier_llm = self.llm.with_structured_output(MessageClassifier)

        result = classifier_llm.invoke(
            [
                {"role": "system", 
                "content": self.system_prompt
                },
                {"role": "user", "content": last_message.content}
            ]
        )

        return {"message_type": result.message_type}
