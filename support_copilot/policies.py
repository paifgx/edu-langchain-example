"""Post-model policy: deterministic safety overrides (SOLID — one responsibility)."""

from __future__ import annotations

import re

from support_copilot.models import Priority, Ticket, TicketAnalysis, TicketCategory


_INJECTION_HINTS = re.compile(
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions|"
    r"you\s+are\s+now\s+dan|system\s+prompt|password\s+reset\s+link|no\s+content\s+policy",
    re.IGNORECASE,
)


def apply_safety_overrides(ticket: Ticket, analysis: TicketAnalysis) -> tuple[TicketAnalysis, list[str]]:
    """
    Force escalation for obvious prompt-injection or embedded system-note abuse.
    Complements the LLM: keeps the pipeline valid even if the model mis-triages.
    """
    notes: list[str] = []
    text = ticket.text
    if _INJECTION_HINTS.search(text):
        notes.append("policy: suspected prompt-injection or jailbreak language")
        analysis = analysis.model_copy(
            update={
                "category": TicketCategory.SECURITY,
                "priority": Priority.CRITICAL,
                "needs_escalation": True,
                "confidence": min(analysis.confidence, 0.55),
                "rationale": analysis.rationale[:1800]
                + " [policy: escalated for injection-like content]",
            }
        )
    if "personenbezogene" in text.lower() and "anderen kunden" in text.lower():
        notes.append("policy: third-party PII leak reported")
        analysis = analysis.model_copy(
            update={
                "category": TicketCategory.SECURITY,
                "priority": Priority.CRITICAL,
                "needs_escalation": True,
            }
        )
    return analysis, notes


def should_escalate(analysis: TicketAnalysis) -> bool:
    """Routing rule: critical/high priority or explicit human handoff."""
    if analysis.needs_escalation:
        return True
    return analysis.priority in {Priority.HIGH, Priority.CRITICAL}
