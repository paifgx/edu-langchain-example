"""CLI entry points for workshop demos (smoke, single pipeline, batch, follow-up)."""

from __future__ import annotations

import argparse
import json
import time

from support_copilot.batch_job import run_batch
from support_copilot.chains import build_pipeline
from support_copilot.config import load_config
from support_copilot.io import load_tickets_jsonl
from support_copilot.memory import (
    bind_session,
    build_follow_up_runnable,
    clear_session_store,
)
from support_copilot.smoke import main as smoke_main


def _cmd_pipeline_one(args: argparse.Namespace) -> None:
    cfg = load_config()
    pipeline = build_pipeline(cfg)
    tickets = load_tickets_jsonl(args.input)
    by_id = {t.id: t for t in tickets}
    ticket = by_id.get(args.ticket_id) or tickets[0]
    t0 = time.perf_counter()
    result = pipeline.invoke(ticket)
    dt = time.perf_counter() - t0
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    print(f"elapsed_s={dt:.3f}")


def _cmd_follow_up_demo(args: argparse.Namespace) -> None:
    clear_session_store()
    cfg = load_config()
    tickets = load_tickets_jsonl(args.input)
    by_id = {t.id: t for t in tickets}
    a = by_id[args.ticket_a]
    b = by_id[args.ticket_b]
    ra = build_follow_up_runnable(cfg, a)
    rb = build_follow_up_runnable(cfg, b)
    sa = bind_session(ra, "session-a")
    sb = bind_session(rb, "session-b")
    sa({"input": args.question_a})
    out_b = sb({"input": args.question_b})
    print("session-b reply (should not leak session-a specifics):\n", out_b.content)
    sa({"input": "What exact detail did I mention first?"})
    out_a2 = sa({"input": "repeat my first question only"})
    print("session-a follow-up:\n", out_a2.content)


def main() -> None:
    parser = argparse.ArgumentParser(prog="support-copilot-demo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="One model call + metadata")
    p_smoke.set_defaults(func=lambda _: smoke_main())

    p_one = sub.add_parser("pipeline-one", help="Run full pipeline on one ticket")
    p_one.add_argument("--input", default="data/tickets.jsonl")
    p_one.add_argument(
        "--ticket-id", default="", help="Ticket id; defaults to first row if empty"
    )
    p_one.set_defaults(func=_cmd_pipeline_one)

    p_batch = sub.add_parser("batch", help="Batch all tickets to reports/")
    p_batch.add_argument("--input", default="data/tickets.jsonl")
    p_batch.add_argument("--reports", default="reports")
    p_batch.add_argument("--max-concurrency", type=int, default=3)

    def _run_batch(ns: argparse.Namespace) -> None:
        run_batch(ns.input, ns.reports, ns.max_concurrency)

    p_batch.set_defaults(func=_run_batch)

    p_fu = sub.add_parser(
        "follow-up", help="Two isolated follow-up sessions (needs API)"
    )
    p_fu.add_argument("--input", default="data/tickets.jsonl")
    p_fu.add_argument("--ticket-a", default="T-1001")
    p_fu.add_argument("--ticket-b", default="T-1007")
    p_fu.add_argument(
        "--question-a",
        default="What is the main urgency in my ticket?",
    )
    p_fu.add_argument(
        "--question-b",
        default="Summarize my ticket in one sentence.",
    )
    p_fu.set_defaults(func=_cmd_follow_up_demo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
