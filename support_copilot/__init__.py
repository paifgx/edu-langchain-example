"""Support Copilot workshop package (Übung 01 — Fundament)."""

from support_copilot.config import AppConfig, build_chat_model, load_config
from support_copilot.models import PipelineResult, Ticket, TicketAnalysis

__all__ = [
    "AppConfig",
    "Ticket",
    "TicketAnalysis",
    "PipelineResult",
    "build_chat_model",
    "load_config",
]
