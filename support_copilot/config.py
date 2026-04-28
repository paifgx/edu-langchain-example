"""Central configuration and model factories (single place for model names)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


ProfileName = Literal["triage", "response"]


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime settings loaded from the environment."""

    openai_api_key: str
    triage_model: str
    response_model: str
    triage_temperature: float
    response_temperature: float
    langchain_tracing_v2: bool
    langchain_project: str | None

    @property
    def langsmith_enabled(self) -> bool:
        return self.langchain_tracing_v2 and bool(
            os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
        )


def load_config() -> AppConfig:
    """Load `.env` and construct config. Optional LangSmith vars must not break runs."""
    load_dotenv()
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in {"1", "true", "yes"}
    return AppConfig(
        openai_api_key=os.environ["OPENAI_API_KEY"],
        triage_model=os.getenv("SUPPORT_COPILOT_TRIAGE_MODEL", "gpt-4o-mini"),
        response_model=os.getenv(
            "SUPPORT_COPILOT_RESPONSE_MODEL",
            os.getenv("SUPPORT_COPILOT_TRIAGE_MODEL", "gpt-4o-mini"),
        ),
        triage_temperature=float(os.getenv("SUPPORT_COPILOT_TRIAGE_TEMPERATURE", "0.1")),
        response_temperature=float(
            os.getenv("SUPPORT_COPILOT_RESPONSE_TEMPERATURE", "0.2")
        ),
        langchain_tracing_v2=tracing,
        langchain_project=os.getenv("LANGCHAIN_PROJECT"),
    )


def build_chat_model(cfg: AppConfig, profile: ProfileName = "triage") -> ChatOpenAI:
    """Create a shared `ChatOpenAI` instance; model name lives only here + env."""
    if profile == "triage":
        return ChatOpenAI(
            model=cfg.triage_model,
            temperature=cfg.triage_temperature,
            api_key=cfg.openai_api_key,
        )
    return ChatOpenAI(
        model=cfg.response_model,
        temperature=cfg.response_temperature,
        api_key=cfg.openai_api_key,
    )


def trace_config(cfg: AppConfig, run_name: str, tags: list[str] | None = None) -> dict:
    """Optional LangSmith metadata; empty when tracing is off."""
    if not cfg.langsmith_enabled:
        return {}
    meta: dict = {"run_name": run_name, "tags": tags or []}
    if cfg.langchain_project:
        meta["metadata"] = {"project": cfg.langchain_project}
    return meta
