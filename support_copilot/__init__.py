"""Support Copilot Fundament — Musterlösung Übung 01."""

from support_copilot.config import CopilotSettings
from support_copilot.domain import PipelineResult, Ticket, TicketAnalysis
from support_copilot.pipeline import SupportTicketPipeline

__all__ = [
    "CopilotSettings",
    "PipelineResult",
    "SupportTicketPipeline",
    "Ticket",
    "TicketAnalysis",
]
