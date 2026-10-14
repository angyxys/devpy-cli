import os

from langchain_ollama import ChatOllama


def _get_base_url() -> str:
    host = os.getenv("OLLAMA_HOST", "localhost")
    port = os.getenv("OLLAMA_PORT", "11434")
    return f"http://{host}:{port}"


def create() -> ChatOllama:
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        base_url=_get_base_url(),
        temperature=0,
    )
