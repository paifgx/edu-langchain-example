"""CLI: Smoke, Einzelticket, Batch, Follow-up-Demo — Musterlösung Übung 01."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from support_copilot.batch_job import TicketBatchJob
from support_copilot.config import ChatModelFactory, CopilotSettings
from support_copilot.follow_up import SupportFollowUpChat
from support_copilot.io import load_all_tickets
from support_copilot.pipeline import SupportTicketPipeline
from support_copilot.smoke import run_smoke


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_one(args: argparse.Namespace) -> int:
    settings = CopilotSettings.load()
    factory = ChatModelFactory(settings)
    pipeline = SupportTicketPipeline(
        factory.triage_llm(), factory.response_llm()).as_runnable()
    tickets = load_all_tickets(Path(args.data))
    ticket = next(t for t in tickets if t.id == args.ticket_id)
    result = pipeline.invoke(ticket, config=settings.default_runnable_config())
    print(result.model_dump_json(indent=2))
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    settings = CopilotSettings.load()
    factory = ChatModelFactory(settings)
    pipeline = SupportTicketPipeline(
        factory.triage_llm(), factory.response_llm()).as_runnable()
    tickets = load_all_tickets(Path(args.data))
    if args.limit:
        tickets = tickets[: args.limit]

    job = TicketBatchJob(pipeline)
    seq_rows, seq_elapsed, seq_usage = job.run_sequential(tickets)
    bat_rows, bat_elapsed, bat_usage = job.run_batch(
        tickets, max_concurrency=args.concurrency)

    report_path = Path(args.out)
    job.execute_and_save(tickets, report_path,
                         max_concurrency=args.concurrency, label="batch")

    seq_rep = TicketBatchJob.build_report(
        tickets, seq_rows, seq_elapsed, seq_usage)
    bat_rep = TicketBatchJob.build_report(
        tickets, bat_rows, bat_elapsed, bat_usage)

    print("=== Einzelverarbeitung (sequentiell) ===")
    print(
        f"Tickets: {seq_rep.ticket_count}  Zeit: {seq_rep.elapsed_seconds:.2f}s")
    print(
        f"Eskaliert (Schätzung): {seq_rep.escalated_count}  Fehler: {len(seq_rep.errors)}")
    print(f"Usage: {seq_rep.usage_by_model}")

    print("=== Batch ===")
    print(
        f"Tickets: {bat_rep.ticket_count}  Zeit: {bat_rep.elapsed_seconds:.2f}s  max_concurrency={args.concurrency}")
    print(
        f"Eskaliert (Schätzung): {bat_rep.escalated_count}  Fehler: {len(bat_rep.errors)}")
    if bat_rep.errors:
        for e in bat_rep.errors:
            print(f"  ! {e}")
    print(f"Usage: {bat_rep.usage_by_model}")
    print(f"Report: {report_path.resolve()}")
    return 0


def cmd_chat_demo(args: argparse.Namespace) -> int:
    settings = CopilotSettings.load()
    factory = ChatModelFactory(settings)
    pipeline = SupportTicketPipeline(
        factory.triage_llm(), factory.response_llm()).as_runnable()
    tickets = load_all_tickets(Path(args.data))
    t_a = next(t for t in tickets if t.id == args.session_a_ticket)
    t_b = next(t for t in tickets if t.id == args.session_b_ticket)

    cfg = settings.default_runnable_config()
    r_a = pipeline.invoke(t_a, config=cfg)
    r_b = pipeline.invoke(t_b, config=cfg)

    chat = SupportFollowUpChat(factory.response_llm())
    s_a, s_b = "session-demo-a", "session-demo-b"

    q_a1 = "Welche Priorität hat dieses Ticket laut Analyse — und warum?"
    q_b1 = "Nenne nur die Ticket-ID, um welches Ticket es hier geht."

    a1 = chat.ask(r_a, q_a1, s_a)
    b1 = chat.ask(r_b, q_b1, s_b)

    q_a2 = "Was war die vorherige Frage in dieser Session? Zitiere sie kurz."
    q_b2 = "Welcher Kunde wurde in Session A genannt? (Sollte unbekannt sein.)"

    a2 = chat.ask(r_a, q_a2, s_a)
    b2 = chat.ask(r_b, q_b2, s_b)

    print("--- Session A (Follow-up) ---")
    print(a1)
    print(a2)
    print("--- Session B (isoliert) ---")
    print(b1)
    print(b2)
    print("\nErwartung: Session B kennt keine Details aus Session A.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Support Copilot — Übung 01 Musterlösung")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("smoke", help="Ein Modellcall + Usage-Metadaten")

    p_one = sub.add_parser("one", help="Pipeline für ein Ticket")
    p_one.add_argument(
        "--data", default=str(_repo_root() / "data" / "tickets.jsonl"))
    p_one.add_argument("--ticket-id", default="T-1001")
    p_one.set_defaults(func=cmd_one)

    p_batch = sub.add_parser("batch", help="Batch + Report unter reports/")
    p_batch.add_argument(
        "--data", default=str(_repo_root() / "data" / "tickets.jsonl"))
    p_batch.add_argument(
        "--out", default=str(_repo_root() / "reports" / "batch_latest.json"))
    p_batch.add_argument("--concurrency", type=int, default=4)
    p_batch.add_argument("--limit", type=int, default=0,
                         help="0 = alle Tickets")
    p_batch.set_defaults(func=cmd_batch)

    p_chat = sub.add_parser(
        "chat-demo", help="Zwei isolierte Follow-up-Sessions")
    p_chat.add_argument(
        "--data", default=str(_repo_root() / "data" / "tickets.jsonl"))
    p_chat.add_argument("--session-a-ticket", default="T-1001")
    p_chat.add_argument("--session-b-ticket", default="T-1007")
    p_chat.set_defaults(func=cmd_chat_demo)

    args = parser.parse_args()
    if args.cmd == "smoke":
        run_smoke()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
