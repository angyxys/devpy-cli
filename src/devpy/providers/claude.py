import os

from langchain_anthropic import ChatAnthropic


def create() -> ChatAnthropic:
    return ChatAnthropic(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
    )
