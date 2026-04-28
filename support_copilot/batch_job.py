"""Batch pipeline execution, reporting, and simple metrics."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from langchain_community.callbacks import get_openai_callback
from langchain_core.runnables import RunnableLambda

from support_copilot.chains import build_pipeline
from support_copilot.config import load_config
from support_copilot.io import load_tickets_jsonl
from support_copilot.models import PipelineResult, Ticket


def _safe_invoke(pipeline, ticket: Ticket) -> PipelineResult | dict:
    try:
        return pipeline.invoke(ticket)
    except Exception as exc:  # noqa: BLE001 — batch must not abort the whole run
        return {"error": str(exc), "ticket_id": ticket.id}


def run_batch(
    tickets_path: str | Path,
    reports_dir: str | Path = "reports",
    max_concurrency: int = 3,
) -> Path:
    cfg = load_config()
    pipeline = build_pipeline(cfg)
    safe = RunnableLambda(lambda t: _safe_invoke(pipeline, t))
    tickets = load_tickets_jsonl(tickets_path)
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    with get_openai_callback() as cb:
        results: list[PipelineResult | dict] = safe.batch(
            tickets,
            config={"max_concurrency": max(1, max_concurrency)},
        )
    elapsed = time.perf_counter() - t0

    errors = [r for r in results if isinstance(r, dict) and "error" in r]
    ok = [r for r in results if isinstance(r, PipelineResult)]
    escalated = sum(1 for r in ok if r.used_escalation_path)

    out = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "tickets_path": str(Path(tickets_path).resolve()),
        "count": len(tickets),
        "elapsed_seconds": round(elapsed, 3),
        "max_concurrency": max_concurrency,
        "token_estimates": {
            "total_tokens": cb.total_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_cost_usd": round(cb.total_cost, 6),
        },
        "escalated": escalated,
        "errors": errors,
        "results": [r.model_dump(mode="json") if isinstance(r, PipelineResult) else r for r in results],
    }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = reports_dir / f"batch_{stamp}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Tickets: {len(tickets)}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Tokens (approx): {cb.total_tokens}  cost USD (approx): {cb.total_cost:.4f}")
    print(f"Escalated: {escalated}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print("  -", e)
    print(f"Wrote: {out_path}")
    return out_path


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Run support copilot batch pipeline.")
    p.add_argument("--input", default="data/tickets.jsonl", help="Path to tickets JSONL")
    p.add_argument("--reports", default="reports", help="Output directory")
    p.add_argument("--max-concurrency", type=int, default=3)
    args = p.parse_args()
    run_batch(args.input, args.reports, args.max_concurrency)


if __name__ == "__main__":
    main()
