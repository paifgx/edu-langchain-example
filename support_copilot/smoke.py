"""Single-call smoke test for model wiring and usage metadata."""

from __future__ import annotations

from support_copilot.config import build_chat_model, load_config, trace_config


def main() -> None:
    cfg = load_config()
    llm = build_chat_model(cfg, "triage")
    cfg_kwargs = trace_config(cfg, "smoke_model_ping", tags=["smoke", "health"])
    msg = llm.invoke("Reply with exactly one word: ok.", config=cfg_kwargs)
    print("content:", getattr(msg, "content", msg))
    meta = getattr(msg, "response_metadata", None)
    if meta:
        print("response_metadata:", meta)


if __name__ == "__main__":
    main()
