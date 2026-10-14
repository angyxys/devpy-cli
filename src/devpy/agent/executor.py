from __future__ import annotations

from typing import TYPE_CHECKING

from devpy.agent.prompts import build_system_prompt
from devpy.agent.tools import create_tools

if TYPE_CHECKING:
    from devpy.agent import AppContext


class AgentExecutor:
    def __init__(self, ctx: AppContext, llm, dry_run: bool = False):
        self._ctx = ctx
        self._llm = llm
        self._dry_run = dry_run
        self._agent = self._build_agent()

    def _build_agent(self):
        from langgraph.prebuilt import create_react_agent

        tools = create_tools(self._ctx)
        mode = self._ctx.config_manager.get_mode()
        system_prompt = build_system_prompt(mode, self._dry_run)

        try:
            return create_react_agent(
                self._llm,
                tools,
                state_modifier=system_prompt,
            )
        except TypeError:
            return create_react_agent(
                self._llm,
                tools,
                prompt=system_prompt,
            )

    def run(self, user_input: str) -> str:
        result = self._agent.invoke(
            {"messages": [("user", user_input)]},
            config={"configurable": {"thread_id": "devpy_session"}},
        )
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return "No response generated"
