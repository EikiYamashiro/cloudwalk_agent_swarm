import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_chat_model():
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
        return init_chat_model(model, model_provider="ollama")

    elif provider == "gemini":
        model = os.getenv("GEMINI_CHAT_MODEL", os.getenv("GCP_CHAT_MODEL", "gemini-2.0-flash"))
        api_key = os.getenv("GOOGLE_API_KEY")

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.2,
        )

    raise ValueError(
        "Unsupported LLM_PROVIDER. Use one of: 'ollama', 'gemini', 'gcp'."
    )
