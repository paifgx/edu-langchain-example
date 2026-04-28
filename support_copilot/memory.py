"""Session-scoped follow-up chat with bounded in-memory history."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from pydantic import Field

from support_copilot.chains import build_follow_up_prompt
from support_copilot.config import AppConfig, build_chat_model, trace_config
from support_copilot.models import Ticket


class BoundedChatMessageHistory(InMemoryChatMessageHistory):
    """In-memory history with a hard cap (replace with Redis/DB in production)."""

    max_messages: int = Field(default=40, ge=4, le=200)

    def add_messages(self, messages: list[BaseMessage]) -> None:
        super().add_messages(messages)
        overflow = len(self.messages) - self.max_messages
        if overflow > 0:
            self.messages = self.messages[overflow:]


_store: dict[str, BoundedChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """No global singleton conversation: history is always keyed by `session_id`."""
    if session_id not in _store:
        _store[session_id] = BoundedChatMessageHistory()
    return _store[session_id]


def clear_session_store() -> None:
    """Test hook."""
    _store.clear()


def build_follow_up_runnable(cfg: AppConfig, ticket: Ticket) -> RunnableWithMessageHistory:
    llm: ChatOpenAI = build_chat_model(cfg, "response")
    prompt = build_follow_up_prompt().partial(
        ticket_id=ticket.id,
        channel=ticket.channel.value,
        ticket_text=ticket.text,
    )
    inner = (prompt | llm).with_config(**trace_config(cfg, "follow_up_chat", ["memory", "follow-up"]))
    return RunnableWithMessageHistory(
        inner,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def bind_session(
    runnable: RunnableWithMessageHistory, session_id: str
) -> Callable[[dict[str, Any],], Any]:
    """Small helper so call sites always pass `session_id` explicitly."""

    def _invoke(payload: dict[str, Any]) -> Any:
        return runnable.invoke(payload, config={"configurable": {"session_id": session_id}})

    return _invoke
