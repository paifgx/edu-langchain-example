"""Nachgelagerte Regeln — ergänzt Modellausgabe, ohne sie zu ersetzen."""

from __future__ import annotations

import re

from support_copilot.domain import Ticket, TicketAnalysis, TicketCategory, TicketPriority


_INJECTION = re.compile(
    r"ignore\s+(all\s+)?previous\s+instructions|you\s+are\s+now\s+[\"']?dan[\"']?|"
    r"system\s+prompt|internal\s+tool|password\s+reset\s+link",
    re.IGNORECASE,
)


def analysis_needs_guard_correction(ticket: Ticket, analysis: TicketAnalysis) -> bool:
    """Heuristische Prüfung: offensichtliche Fälle müssen eskalieren."""
    text = ticket.text
    if _INJECTION.search(text):
        return not analysis.requires_escalation
    if analysis.category == TicketCategory.SECURITY and not analysis.requires_escalation:
        return True
    # PII-Fremddaten: typisches Schulungsbeispiel aus der Übung
    if "personenbezogene" in text.lower() and "anderen kunden" in text.lower():
        return not analysis.requires_escalation
    if "versehentlich personenbezogene" in text.lower():
        return not analysis.requires_escalation
    return False


def apply_escalation_guard(ticket: Ticket, analysis: TicketAnalysis) -> TicketAnalysis:
    """Setzt Eskalation konservativ, wenn Heuristik anspringt."""
    if not analysis_needs_guard_correction(ticket, analysis):
        return analysis
    return analysis.model_copy(
        update={
            "requires_escalation": True,
            "priority": (
                TicketPriority.CRITICAL
                if analysis.priority != TicketPriority.CRITICAL
                else analysis.priority
            ),
            "category": TicketCategory.SECURITY
            if analysis.category != TicketCategory.SECURITY
            else analysis.category,
            "rationale": analysis.rationale
            + " [policy: heuristic escalation for security/compliance]",
        }
    )
