"""Alle Zeilen in data/tickets.jsonl müssen valide Ticket-Modelle sein."""

from pathlib import Path

import pytest

from support_copilot.domain import Ticket
from support_copilot.io import iter_tickets_jsonl, load_all_tickets


def _data_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "tickets.jsonl"


def test_load_all_tickets_min_count() -> None:
    tickets = load_all_tickets(_data_path())
    assert len(tickets) >= 8


def test_each_line_validates() -> None:
    for t in iter_tickets_jsonl(_data_path()):
        assert isinstance(t, Ticket)
        assert t.id
        assert t.text.strip()


@pytest.mark.parametrize(
    "ticket_id",
    ["T-1005", "T-1007", "T-1018"],
)
def test_security_or_injection_present(ticket_id: str) -> None:
    tickets = {t.id: t for t in load_all_tickets(_data_path())}
    assert ticket_id in tickets
