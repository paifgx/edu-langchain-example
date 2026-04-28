"""Domain models — enums + Pydantic schemas for structured I/O."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Channel(str, Enum):
    EMAIL = "email"
    CHAT = "chat"
    PORTAL = "portal"


class TicketCategory(str, Enum):
    BILLING = "Billing"
    BUG = "Bug"
    HOW_TO = "How-to"
    SECURITY = "Security"
    VERTRAG = "Vertrag"
    SONSTIGES = "Sonstiges"


class Priority(str, Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    CRITICAL = "Critical"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"


class Ticket(BaseModel):
    id: str
    customer_name: str | None = None
    channel: Channel
    text: str

    @field_validator("customer_name")
    @classmethod
    def empty_name_to_none(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v


class TicketAnalysis(BaseModel):
    category: TicketCategory
    priority: Priority
    sentiment: Sentiment
    language: str = Field(..., min_length=2, max_length=32)
    needs_escalation: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=8, max_length=2000)

    @field_validator("rationale")
    @classmethod
    def rationale_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("rationale must not be empty")
        return v.strip()


class KeywordSet(BaseModel):
    terms: list[str] = Field(..., min_length=1, max_length=5)

    @field_validator("terms")
    @classmethod
    def normalize_terms(cls, terms: list[str]) -> list[str]:
        out = [t.strip() for t in terms if t and t.strip()]
        if not out:
            raise ValueError("at least one keyword required")
        if len(out) > 5:
            raise ValueError("at most 5 keywords")
        return out


class ShortSummary(BaseModel):
    text: str = Field(..., min_length=16, max_length=800)


class SupportDraft(BaseModel):
    """Either customer-facing reply text or an internal escalation note."""

    audience: Literal["customer", "internal"]
    body: str = Field(..., min_length=1, max_length=8000)
    next_action: str = Field(..., min_length=2, max_length=500)


class PipelineResult(BaseModel):
    ticket: Ticket
    analysis: TicketAnalysis
    keywords: KeywordSet
    summary: str
    draft: SupportDraft
    used_escalation_path: bool
    policy_notes: list[str] = Field(default_factory=list)
