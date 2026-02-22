import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from utils.agents.agent_base import AgentBase, State
from utils.factory.llm import get_chat_model
from utils.factory.retriever import format_context, retriever
from utils.tools.search import google_web_search


class KnowledgeAgent(AgentBase):

    def __init__(self):
        super().__init__(tools=[], system_prompt="Knowledge Agent")
        self.rag_llm = get_chat_model()

    def invoke(self, state: State):
        conversation = self._build_conversation(state, limit=8)
        if not conversation:
            return {"messages": [{"role": "assistant", "content": "Please send a question."}]}

        question = conversation[-1]["content"]
        history_lines = [
            f"{item['role']}: {item['content']}" for item in conversation[:-1]
        ]
        history = "\n".join(history_lines) if history_lines else "No previous messages."
        min_relevance = 0.52
        vectorstore = getattr(retriever, "vectorstore", None)

        top4 = []
        if vectorstore and hasattr(vectorstore, "similarity_search_with_relevance_scores"):
            top4 = vectorstore.similarity_search_with_relevance_scores(question, k=4)
        elif vectorstore and hasattr(vectorstore, "similarity_search_with_score"):
            raw = vectorstore.similarity_search_with_score(question, k=4)
            top4 = [(doc, 1.0 / (1.0 + float(distance))) for doc, distance in raw]

        relevant_docs = [doc for doc, score in top4 if score > min_relevance]

        if relevant_docs:
            context = format_context(relevant_docs)
            prompt = ChatPromptTemplate.from_template(
                """
Use only the retrieved InfinitePay context to answer the question.
Answer in English by default.
If the user explicitly writes in another language, answer in that language.
Use the recent chat history when the question references previous messages.

Recent chat history:
{history}

Context:
{context}

Question:
{question}
"""
            )
            answer = (prompt | self.rag_llm | StrOutputParser()).invoke(
                {"history": history, "context": context, "question": question}
            )
        else:
            web_context = google_web_search.invoke({"question": question})
            prompt = ChatPromptTemplate.from_template(
                """
Use the web search results to answer the user question objectively.
Answer in English by default.
If the user explicitly writes in another language, answer in that language.
Use the recent chat history when the question references previous messages.

Recent chat history:
{history}

Web results:
{web_context}

Question:
{question}
"""
            )
            answer = (prompt | self.rag_llm | StrOutputParser()).invoke(
                {"history": history, "web_context": web_context, "question": question}
            )

        return {"messages": [{"role": "assistant", "content": answer}]}
