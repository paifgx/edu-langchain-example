"""Batch-Läufe, Reporting, Nutzungsmetadaten."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.runnables import Runnable

from support_copilot.domain import PipelineResult, Ticket
from support_copilot.io import write_report_json


@dataclass
class BatchRunReport:
    ticket_count: int
    elapsed_seconds: float
    escalated_count: int
    errors: list[str] = field(default_factory=list)
    usage_by_model: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)


def _serialize_pipeline_result(r: PipelineResult) -> dict[str, Any]:
    return {
        "ticket": r.ticket.model_dump(mode="json"),
        "analysis": r.analysis.model_dump(mode="json"),
        "keywords": r.keywords.model_dump(mode="json"),
        "summary": r.summary,
        "draft": r.draft.model_dump(mode="json"),
    }


def _count_escalated(rows: list[PipelineResult]) -> int:
    n = 0
    for row in rows:
        if row.draft.mode == "internal_escalation" or row.analysis.requires_escalation:
            n += 1
    return n


class TicketBatchJob:
    """Führt dieselbe Pipeline im Einzel- und Batch-Modus aus (return_exceptions)."""

    def __init__(self, pipeline: Runnable[Any, PipelineResult]) -> None:
        self._pipeline = pipeline

    def run_sequential(self, tickets: list[Ticket]) -> tuple[list[PipelineResult | BaseException], float, UsageMetadataCallbackHandler]:
        usage = UsageMetadataCallbackHandler()
        t0 = time.perf_counter()
        out: list[PipelineResult | BaseException] = []
        for ticket in tickets:
            try:
                out.append(self._pipeline.invoke(
                    ticket, config={"callbacks": [usage]}))
            except Exception as e:  # noqa: BLE001
                out.append(e)
        return out, time.perf_counter() - t0, usage

    def run_batch(
        self,
        tickets: list[Ticket],
        *,
        max_concurrency: int = 4,
    ) -> tuple[list[PipelineResult | BaseException], float, UsageMetadataCallbackHandler]:
        usage = UsageMetadataCallbackHandler()
        t0 = time.perf_counter()
        rows = self._pipeline.batch(
            tickets,
            config={"max_concurrency": max_concurrency, "callbacks": [usage]},
            return_exceptions=True,
        )
        return rows, time.perf_counter() - t0, usage

    @staticmethod
    def build_report(
        tickets: list[Ticket],
        rows: list[PipelineResult | BaseException],
        elapsed: float,
        usage: UsageMetadataCallbackHandler,
    ) -> BatchRunReport:
        errors: list[str] = []
        for i, row in enumerate(rows):
            if isinstance(row, BaseException):
                tid = tickets[i].id if i < len(tickets) else "?"
                errors.append(f"{tid}: {row!r}")
        ok = [r for r in rows if isinstance(r, PipelineResult)]
        return BatchRunReport(
            ticket_count=len(tickets),
            elapsed_seconds=elapsed,
            escalated_count=_count_escalated(ok),
            errors=errors,
            usage_by_model=dict(usage.usage_metadata),
            results=[_serialize_pipeline_result(r) for r in ok],
        )

    def execute_and_save(
        self,
        tickets: list[Ticket],
        report_path: Path,
        *,
        max_concurrency: int = 4,
        label: str = "batch",
    ) -> BatchRunReport:
        rows, elapsed, usage = self.run_batch(
            tickets, max_concurrency=max_concurrency)
        report = self.build_report(tickets, rows, elapsed, usage)
        payload: dict[str, Any] = {
            "label": label,
            "ticket_count": report.ticket_count,
            "elapsed_seconds": report.elapsed_seconds,
            "escalated_count": report.escalated_count,
            "errors": report.errors,
            "usage_by_model": report.usage_by_model,
            "results": report.results,
        }
        write_report_json(report_path, payload)
        return report
