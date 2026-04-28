"""Session-isolierte Follow-up-Chats mit begrenzter History."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel, Field

from support_copilot.domain import PipelineResult


_EMAIL_RE = re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-/.]{7,}\d")


def redact_pii(text: str) -> str:
    """Einfache Redaktion für Demo/Übung (kein vollständiger DLP-Ersatz)."""
    text = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    return _PHONE_RE.sub("[REDACTED-PHONE]", text)


class BoundedChatMessageHistory(BaseChatMessageHistory, BaseModel):
    """In-Memory-History mit harter Obergrenze (kein unbounded Wachstum)."""

    messages: list[BaseMessage] = Field(default_factory=list)
    max_messages: int = 24

    def add_messages(self, messages: list[BaseMessage]) -> None:
        self.messages.extend(messages)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def clear(self) -> None:
        self.messages = []


class SessionHistoryStore:
    """Factory für RunnableWithMessageHistory — strikt nach session_id getrennt."""

    def __init__(self) -> None:
        self._sessions: dict[str, BoundedChatMessageHistory] = {}

    def get(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = BoundedChatMessageHistory()
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class SupportFollowUpChat:
    """Beantwortet Rückfragen zu einem bereits analysierten Ticket (kontextgebunden)."""

    def __init__(self, response_llm: BaseChatModel, history_store: SessionHistoryStore | None = None) -> None:
        self._llm = response_llm
        self._store = history_store or SessionHistoryStore()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Du bist ein Support-Assistenz-Modul. Du beziehst dich ausschließlich auf das "
                    "folgende Ticket und die interne Analyse. Wenn eine Frage außerhalb dieses Kontexts liegt, "
                    "weise höflich darauf hin.\n\n"
                    "Ticket (PII ggf. redigiert):\n{ticket_block}\n\n"
                    "Analyse:\n{analysis_block}\n\n"
                    "Kurzsummary:\n{summary}\n",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        inner: Runnable = prompt | self._llm.with_config(
            run_name="follow_up_llm") | StrOutputParser()
        self._runnable = RunnableWithMessageHistory(
            inner,
            self._store.get,
            input_messages_key="question",
            history_messages_key="history",
        ).with_config(run_name="support_follow_up_chat")

    @property
    def store(self) -> SessionHistoryStore:
        return self._store

    def build_input(self, result: PipelineResult, question: str) -> dict[str, str]:
        return {
            "ticket_block": redact_pii(result.ticket.model_dump_json(indent=2)),
            "analysis_block": redact_pii(result.analysis.model_dump_json(indent=2)),
            "summary": redact_pii(result.summary),
            "question": question.strip(),
        }

    def ask(self, result: PipelineResult, question: str, session_id: str) -> str:
        cfg: dict[str, Any] = {"configurable": {"session_id": session_id}}
        payload = self.build_input(result, question)
        return str(self._runnable.invoke(payload, config=cfg))

    def as_runnable(self) -> RunnableWithMessageHistory:
        return self._runnable
