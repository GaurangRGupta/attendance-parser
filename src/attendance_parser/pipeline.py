"""Load a detailed dump and produce the monthly-style Report."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from attendance_parser.extract import extract_document
from attendance_parser.models import Report
from attendance_parser.normalize import normalize_slots
from attendance_parser.summarize import summarize


def build_report(
    path: str | Path,
    *,
    lab_batches: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    threshold: float = 0.8,
) -> Report:
    extracted = extract_document(path)
    slots = normalize_slots(extracted.slots, lab_batches=lab_batches)
    return summarize(
        extracted.student,
        slots,
        window_from=date_from,
        window_to=date_to,
        threshold=threshold,
        lab_batches=lab_batches,
    )
