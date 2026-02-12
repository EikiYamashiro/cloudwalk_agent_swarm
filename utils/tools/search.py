import http.client
import json
import os
from langchain_core.tools import tool

def _serper_search(query: str) -> dict:
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Web Search indisponivel: configure SERPER_API_KEY para usar o Serper."
        )

    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    try:
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        raw = res.read().decode("utf-8")
    finally:
        conn.close()

    if res.status >= 400:
        raise RuntimeError(f"Serper falhou (HTTP {res.status}): {raw}")

    return json.loads(raw)


@tool
def google_web_search(question: str) -> str:
    """Search Google using Serper and return the top results."""
    try:
        data = _serper_search(question)
    except Exception as exc:
        return str(exc)

    answer_box = data.get("answerBox")
    if answer_box:
        answer = (
            answer_box.get("answer")
            or answer_box.get("snippet")
            or answer_box.get("title")
        )
        if answer:
            return f"Resposta rapida: {answer}"

    organic = data.get("organic", []) or []
    if not organic:
        return "Nao encontrei resultados relevantes no Google."

    lines = []
    for idx, item in enumerate(organic[:5], start=1):
        title = item.get("title", "Sem titulo")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        lines.append(
            f"[Resultado {idx}] {title}\nFonte: {link}\nResumo: {snippet}"
        )
    return "\n\n".join(lines)