"""Pull student header and hour-rows out of a detailed SAP attendance PDF."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pdfplumber

from attendance_parser.errors import ParseError
from attendance_parser.models import ExtractedDocument, RawSlot, Student

_DATE_ROW = "%b %d, %Y"
_DATE_HEADER = "%d.%m.%Y"

_DURATION_RE = re.compile(
    r"From\s+(\d{2}\.\d{2}\.\d{4})\s+to\s+(\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)
_SESSION_RE = re.compile(
    r"Academic Year\s*&\s*Academic Session\s+(.+)",
    re.IGNORECASE,
)


def extract_document(path: str | Path) -> ExtractedDocument:
    path = Path(path)
    if not path.is_file():
        raise ParseError(f"File not found: {path}")

    with pdfplumber.open(path) as doc:
        if not doc.pages:
            raise ParseError(f"PDF has no pages: {path}")
        header_text = doc.pages[0].extract_text() or ""
        student = _parse_student(header_text)
        slots = _parse_slots(doc.pages)

    _assert_contiguous(slots)
    return ExtractedDocument(student=student, slots=slots)


def _parse_student(text: str) -> Student:
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    if not lines:
        raise ParseError("Could not read student header from the first page.")

    college = lines[0]
    fields: dict[str, str] = {}
    for line in lines:
        for label, key in (
            ("Student Name", "name"),
            ("Student Number", "number"),
            ("Roll No.", "roll"),
            ("Program Name", "program"),
        ):
            if line.lower().startswith(label.lower()):
                fields[key] = line[len(label) :].strip(" :")
                break

    session_line = next((ln for ln in lines if "academic year" in ln.lower()), "")
    session_match = _SESSION_RE.search(session_line)
    year = ""
    session = ""
    if session_match:
        raw = session_match.group(1).strip()
        if "," in raw:
            year, session = (part.strip() for part in raw.split(",", 1))
        else:
            year = raw

    duration_line = next((ln for ln in lines if "duration" in ln.lower() or "from" in ln.lower()), "")
    duration = _DURATION_RE.search(duration_line) or _DURATION_RE.search(text)
    if not duration:
        raise ParseError("Could not parse attendance report duration.")

    missing = [k for k in ("name", "number", "roll", "program") if not fields.get(k)]
    if missing:
        raise ParseError(f"Missing header field(s): {', '.join(missing)}")

    return Student(
        name=fields["name"],
        number=fields["number"],
        roll=fields["roll"],
        academic_year=year,
        academic_session=session,
        program=fields["program"],
        college=college,
        report_from=_parse_header_date(duration.group(1)),
        report_to=_parse_header_date(duration.group(2)),
    )


def _parse_header_date(value: str):
    try:
        return datetime.strptime(value, _DATE_HEADER).date()
    except ValueError as exc:
        raise ParseError(f"Unrecognised header date: {value!r}") from exc


def _parse_slots(pages) -> list[RawSlot]:
    slots: list[RawSlot] = []
    for page in pages:
        for table in page.extract_tables() or []:
            if not table:
                continue
            for row in table:
                slot = _row_to_slot(row)
                if slot is not None:
                    slots.append(slot)
    if not slots:
        raise ParseError("No attendance rows found in the PDF.")
    return slots


def _row_to_slot(row: list | None) -> RawSlot | None:
    if not row or len(row) < 6:
        return None
    sr_raw = _cell(row[0])
    if not sr_raw.isdigit():
        return None
    course = _cell(row[1])
    date_raw = _cell(row[2])
    start = _cell(row[3])
    end = _cell(row[4])
    status = _cell(row[5]).upper()
    if not course or not date_raw or not status:
        raise ParseError(f"Incomplete attendance row {sr_raw}: {row!r}")
    try:
        day = datetime.strptime(date_raw, _DATE_ROW).date()
    except ValueError as exc:
        raise ParseError(f"Unrecognised row date in Sr {sr_raw}: {date_raw!r}") from exc
    return RawSlot(
        sr=int(sr_raw),
        course_raw=course,
        date=day,
        start=start,
        end=end,
        status=status,
    )


def _cell(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _assert_contiguous(slots: list[RawSlot]) -> None:
    numbers = [s.sr for s in slots]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise ParseError(
            f"Attendance serial numbers are not contiguous 1..{len(numbers)} "
            f"(got {numbers[0]}..{numbers[-1]}, {len(numbers)} rows)."
        )
