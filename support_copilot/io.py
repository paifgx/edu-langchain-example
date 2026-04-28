"""Ein-/Ausgabe: Tickets aus JSONL laden, Reports schreiben."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from pydantic import TypeAdapter

from support_copilot.domain import Ticket


def iter_tickets_jsonl(path: Path) -> Iterator[Ticket]:
    adapter = TypeAdapter(Ticket)
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                msg = f"{path}:{line_no}: ungültiges JSON"
                raise ValueError(msg) from e
            yield adapter.validate_python(data)


def load_all_tickets(path: Path) -> list[Ticket]:
    return list(iter_tickets_jsonl(path))


def write_report_json(path: Path, payload: dict[str, object] | list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
