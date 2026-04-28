"""JSONL ticket loading."""

from __future__ import annotations

import json
from pathlib import Path

from support_copilot.models import Ticket


def load_tickets_jsonl(path: str | Path) -> list[Ticket]:
    path = Path(path)
    tickets: list[Ticket] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                tickets.append(Ticket.model_validate_json(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from e
    return tickets
