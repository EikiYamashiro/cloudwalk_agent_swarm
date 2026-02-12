import hashlib
import os
import re
import shutil
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

load_dotenv()

URLS = [
    "https://www.infinitepay.io",
    "https://www.infinitepay.io/maquininha",
    "https://www.infinitepay.io/maquininha-celular",
    "https://www.infinitepay.io/tap-to-pay",
    "https://www.infinitepay.io/pdv",
    "https://www.infinitepay.io/receba-na-hora",
    "https://www.infinitepay.io/gestao-de-cobranca-2",
    "https://www.infinitepay.io/gestao-de-cobranca",
    "https://www.infinitepay.io/link-de-pagamento",
    "https://www.infinitepay.io/loja-online",
    "https://www.infinitepay.io/boleto",
    "https://www.infinitepay.io/conta-digital",
    "https://www.infinitepay.io/conta-pj",
    "https://www.infinitepay.io/pix",
    "https://www.infinitepay.io/pix-parcelado",
    "https://www.infinitepay.io/emprestimo",
    "https://www.infinitepay.io/cartao",
    "https://www.infinitepay.io/rendimento",
]

DB_LOCATION = "./chroma_infinitepay_db"
COLLECTION_NAME = "infinitepay_pages"
SIGNATURE_FILE = "sources.sha256"
EMBED_MODEL = "mxbai-embed-large"


def get_embeddings():
    provider = os.getenv("EMBEDDING_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).strip().lower()

    if provider == "ollama":
        model = os.getenv("OLLAMA_EMBED_MODEL", EMBED_MODEL)
        return OllamaEmbeddings(model=model)

    if provider in {"gemini", "gcp"}:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError as exc:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=gemini requires 'langchain-google-genai'. "
                "Install it with: pip install langchain-google-genai"
            ) from exc

        model = os.getenv("GEMINI_EMBED_MODEL")
        api_key = os.getenv("GOOGLE_API_KEY")
        return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)

    raise ValueError(
        "Unsupported EMBEDDING_PROVIDER. Use one of: 'ollama', 'gemini', 'gcp'."
    )

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()



def fetch_page(url: str) -> Document | None:
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = normalize_text(soup.title.get_text()) if soup.title else url
    content = normalize_text(soup.get_text(separator=" "))
    if len(content) < 120:
        print(f"[WARN] Conteudo muito curto em {url}, pulando.")
        return None

    return Document(
        page_content=f"{title}\n\n{content}",
        metadata={"source": url, "title": title},
    )

def build_source_signature(urls: list[str]) -> str:
    unique_urls = sorted(set(urls))
    return hashlib.sha256("\n".join(unique_urls).encode("utf-8")).hexdigest()

def load_documents(urls: list[str]) -> list[Document]:
    docs = []
    for url in urls:
        document = fetch_page(url)
        if document is not None:
            docs.append(document)
    return docs

def init_retriever(force_reindex: bool = False):
    signature = build_source_signature(URLS)
    signature_path = Path(DB_LOCATION) / SIGNATURE_FILE

    needs_reindex = force_reindex or not Path(DB_LOCATION).exists()
    if not needs_reindex and signature_path.exists():
        existing_signature = signature_path.read_text(encoding="utf-8").strip()
        needs_reindex = existing_signature != signature

    if needs_reindex and Path(DB_LOCATION).exists():
        shutil.rmtree(DB_LOCATION)

    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=DB_LOCATION,
        embedding_function=embeddings,
    )

    if needs_reindex:
        print("[INFO] Reindexando base com scraping dos sites...")
        raw_documents = load_documents(URLS)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
        )
        documents = splitter.split_documents(raw_documents)
        ids = [f"doc_{i}" for i in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=ids)
        signature_path.parent.mkdir(parents=True, exist_ok=True)
        signature_path.write_text(signature, encoding="utf-8")
        print(f"[INFO] Indexacao concluida. Chunks: {len(documents)}")
    else:
        print("[INFO] Usando indice existente.")

    return vector_store.as_retriever(search_kwargs={"k": 4})

def format_context(documents: list[Document]) -> str:
    sections = []
    for idx, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "desconhecido")
        title = doc.metadata.get("title", "Sem titulo")
        sections.append(
            f"[Trecho {idx}] {title}\nFonte: {source}\nConteudo: {doc.page_content}"
        )
    return "\n\n".join(sections)

retriever = init_retriever()
