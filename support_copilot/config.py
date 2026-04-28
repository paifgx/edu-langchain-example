"""Zentrale Konfiguration: .env, Modellprofile, optionales LangSmith."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Ein benanntes LLM-Profil (z. B. günstig vs. stärker)."""

    name: str
    model: str
    temperature: float = 0.0


@dataclass(frozen=True, slots=True)
class CopilotSettings:
    """Alle Laufzeitparameter aus Umgebungsvariablen."""

    triage: ModelProfile
    response: ModelProfile
    langchain_tracing_v2: bool
    langchain_project: str | None

    @staticmethod
    def load() -> CopilotSettings:
        load_dotenv(override=False)
        triage_model = os.getenv("OPENAI_MODEL_TRIAGE") or os.getenv(
            "OPENAI_MODEL", "gpt-4o-mini")
        response_model = os.getenv("OPENAI_MODEL_RESPONSE") or os.getenv(
            "OPENAI_MODEL", triage_model)
        triage_temp = float(os.getenv("OPENAI_TEMPERATURE_TRIAGE", "0"))
        response_temp = float(os.getenv("OPENAI_TEMPERATURE_RESPONSE", "0.2"))

        tracing = os.getenv("LANGCHAIN_TRACING_V2",
                            "").lower() in ("true", "1", "yes")
        project = os.getenv("LANGCHAIN_PROJECT") or None

        return CopilotSettings(
            triage=ModelProfile("triage", triage_model, triage_temp),
            response=ModelProfile("response", response_model, response_temp),
            langchain_tracing_v2=tracing,
            langchain_project=project,
        )

    def tracing_tags(self) -> list[str]:
        tags = ["support-copilot", "uebung-01"]
        if self.langchain_project:
            tags.append(f"project:{self.langchain_project}")
        return tags

    def default_runnable_config(self) -> dict[str, Any]:
        """Optionale Metadaten für Traces — harmlos ohne LangSmith."""
        cfg: dict[str, Any] = {
            "tags": self.tracing_tags(),
            "metadata": {"app": "support-copilot-fundament"},
        }
        if self.langchain_project:
            cfg["metadata"]["langsmith_project"] = self.langchain_project
        return cfg


class ChatModelFactory:
    """Kapselt Erzeugung der Chat-Modelle (Single Place für Modellnamen)."""

    def __init__(self, settings: CopilotSettings) -> None:
        self._settings = settings

    def triage_llm(self) -> BaseChatModel:
        p = self._settings.triage
        return ChatOpenAI(model=p.model, temperature=p.temperature)

    def response_llm(self) -> BaseChatModel:
        p = self._settings.response
        return ChatOpenAI(model=p.model, temperature=p.temperature)
