from pathlib import Path

from support_copilot.io import load_tickets_jsonl
from support_copilot.models import Ticket


def test_all_jsonl_lines_validate() -> None:
    root = Path(__file__).resolve().parents[1]
    tickets = load_tickets_jsonl(root / "data" / "tickets.jsonl")
    assert len(tickets) >= 8
    for t in tickets:
        assert isinstance(t, Ticket)
        assert t.id
        assert t.text.strip()
