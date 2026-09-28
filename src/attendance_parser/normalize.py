"""Split SAP course codes into subject, THEO/PRAC, and lab batch."""

from __future__ import annotations

import re

from attendance_parser.errors import ParseError
from attendance_parser.models import RawSlot, Slot

# T1 / P1 (or T2, P2, …) is glued to the subject with no space.
_COURSE_RE = re.compile(r"^(?P<subject>.+?)(?P<kind>T\d+|P\d+)(?P<rest>.*)$")
# Trailing letter+digits tag on a P-row (J1, A2, B12, …). Not always J-prefixed.
_BATCH_RE = re.compile(r"([A-Za-z]+\d+)\s*$")

# Official monthly-report titles for subjects in this SAP dump.
TITLE_MAP = {
    "Advanced Database Mgmt System": "ADVANCED DATABASE MANAGEMENT SYSTEMS",
    "Reinforcement Learning": "REINFORCEMENT LEARNING",
    "Neural Networks & Deep Learning": "NEURAL NETWORKS AND DEEP LEARNING",
    "Speech & NaturalLanguageProcessin": "SPEECH AND NATURAL LANGUAGE PROCESSING",
    "Big Data Analytics": "BIG DATA ANALYTICS",
    "MLOps": "MLOPS",
    "Introduction toLinguistics": "INTRODUCTION TO LINGUISTICS",
}

THEO = "THEO"
PRAC = "PRAC"


def normalize_slots(
    raw_slots: list[RawSlot],
    lab_batches: list[str] | None = None,
) -> list[Slot]:
    wanted = {b.strip().upper() for b in (lab_batches or []) if b and b.strip()}
    out: list[Slot] = []
    for raw in raw_slots:
        slot = _normalize_one(raw)
        if (
            slot.lecture_type == PRAC
            and slot.batch
            and wanted
            and slot.batch.upper() not in wanted
        ):
            continue
        out.append(slot)
    return out


def _normalize_one(raw: RawSlot) -> Slot:
    match = _COURSE_RE.match(raw.course_raw)
    if not match:
        raise ParseError(f"Cannot parse course name {raw.course_raw!r} (Sr {raw.sr}).")
    subject = match.group("subject").strip()
    kind = match.group("kind")
    rest = match.group("rest") or ""
    lecture_type = THEO if kind.upper().startswith("T") else PRAC
    batch_match = _BATCH_RE.search(rest.strip())
    batch = batch_match.group(1).upper() if batch_match else None
    return Slot(
        sr=raw.sr,
        course_raw=raw.course_raw,
        date=raw.date,
        start=raw.start,
        end=raw.end,
        status=raw.status,
        subject=subject,
        lecture_type=lecture_type,
        batch=batch,
        display_name=display_title(subject),
    )


def display_title(subject: str) -> str:
    if subject in TITLE_MAP:
        return TITLE_MAP[subject]
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", subject)
    return spaced.upper()
