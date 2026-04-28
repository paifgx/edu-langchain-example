"""Fachliche Pydantic-Modelle — enge Taxonomien, validierbare Testdaten."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TicketChannel(str, Enum):
    EMAIL = "email"
    CHAT = "chat"
    PORTAL = "portal"


class TicketCategory(str, Enum):
    BILLING = "Billing"
    BUG = "Bug"
    HOW_TO = "How-to"
    SECURITY = "Security"
    CONTRACT = "Vertrag"
    OTHER = "Sonstiges"


class TicketPriority(str, Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class Ticket(BaseModel):
    id: str
    customer_name: str | None = None
    channel: TicketChannel
    text: str

    @field_validator("customer_name")
    @classmethod
    def strip_blank_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class TicketAnalysis(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    sentiment: TicketSentiment
    language: str = Field(
        ...,
        description="ISO-Sprachcode oder Kurzname, z. B. de, en, fr",
        max_length=32,
    )
    requires_escalation: bool = Field(
        ...,
        description="True bei Security, PII-Leak, Prompt-Injection, rechtlichen Themen, Vertragskündigung.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=8, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def rationale_not_empty(cls, v: str) -> str:
        t = v.strip()
        if len(t) < 8:
            msg = "Begründung zu kurz."
            raise ValueError(msg)
        return t


class TicketKeywords(BaseModel):
    terms: list[str] = Field(..., min_length=1, max_length=5)

    @field_validator("terms")
    @classmethod
    def normalize_terms(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for t in v:
            s = t.strip()
            if s and s not in out:
                out.append(s)
        if not out:
            msg = "Mindestens ein Keyword erforderlich."
            raise ValueError(msg)
        return out[:5]


class ResponseDraft(BaseModel):
    """Kundenantwort oder interne Eskalationsnotiz plus nächste Aktion."""

    mode: Literal["customer_reply", "internal_escalation"]
    body: str = Field(..., min_length=10, max_length=8000)
    next_action: str = Field(..., min_length=5, max_length=2000)


class PipelineResult(BaseModel):
    """Ergebnisobjekt für Reporting — Originalticket bleibt erhalten."""

    ticket: Ticket
    analysis: TicketAnalysis
    keywords: TicketKeywords
    summary: str
    draft: ResponseDraft
