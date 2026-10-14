import os

from dotenv import load_dotenv


def create_llm():
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if provider == "deepseek":
        from devpy.providers.deepseek import create
        return create()
    elif provider == "claude":
        from devpy.providers.claude import create
        return create()
    elif provider == "google":
        from devpy.providers.google import create
        return create()
    elif provider == "chatgpt":
        from devpy.providers.chatgpt import create
        return create()
    elif provider == "ollama":
        from devpy.providers.ollama import create
        return create()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            "Set LLM_PROVIDER in .env to one of: deepseek, claude, google, chatgpt, ollama"
        )
