"""Smoke-Test: ein Modellcall mit Nutzungsmetadaten (Aufgabe 1)."""

from __future__ import annotations

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage

from support_copilot.config import ChatModelFactory, CopilotSettings


def run_smoke() -> None:
    settings = CopilotSettings.load()
    factory = ChatModelFactory(settings)
    llm = factory.triage_llm()
    usage = UsageMetadataCallbackHandler()
    base_cfg = settings.default_runnable_config()
    msg = HumanMessage(content="Antworte exakt mit einem Wort: OK")
    out = llm.invoke(
        [msg],
        config={
            **base_cfg,
            "run_name": "smoke_openai_ping",
            "callbacks": [usage],
        },
    )
    print("--- Smoke: Modellantwort ---")
    print(getattr(out, "content", out))
    print("--- Smoke: response_metadata (Auszug) ---")
    md = getattr(out, "response_metadata", {}) or {}
    for k in ("model_name", "token_usage", "finish_reason"):
        if k in md:
            print(f"  {k}: {md[k]}")
    print("--- Smoke: UsageMetadataCallbackHandler ---")
    print(usage.usage_metadata or "(keine usage_metadata vom Provider)")
    print("--- Profile ---")
    print(
        f"  triage:   {settings.triage.model} @ T={settings.triage.temperature}")
    print(
        f"  response: {settings.response.model} @ T={settings.response.temperature}")


if __name__ == "__main__":
    run_smoke()
