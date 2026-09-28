"""JSON sidecar for the monthly-style summary."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from attendance_parser.models import Report
from attendance_parser.summarize import format_header_date


def report_to_dict(report: Report) -> dict:
    payload = asdict(report)
    student = payload["student"]
    student["report_from"] = format_header_date(report.student.report_from)
    student["report_to"] = format_header_date(report.student.report_to)
    return payload


def write_json(report: Report, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report_to_dict(report), indent=2), encoding="utf-8")
    return path
