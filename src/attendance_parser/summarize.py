"""Aggregate hour-rows into the college monthly-summary figures."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from datetime import datetime as dt

from attendance_parser.models import (
    ComponentRow,
    CourseSummary,
    Report,
    Slot,
    Student,
)
from attendance_parser.normalize import PRAC, THEO

# P present, A absent, E exemption (counts present), L late admission (ignore),
# NU not updated (exclude from official table).
_CONDUCTED = frozenset({"P", "A", "E"})
_ATTENDED = frozenset({"P", "E"})
_COMPONENT_ORDER = (PRAC, THEO)


def summarize(
    student: Student,
    slots: list[Slot],
    window_from: date | None = None,
    window_to: date | None = None,
    threshold: float = 0.8,
    lab_batches: list[str] | None = None,
) -> Report:
    start = window_from or student.report_from
    end = window_to or student.report_to
    windowed = [s for s in slots if start <= s.date <= end]
    official = [s for s in windowed if s.status in _CONDUCTED]
    pending_nu = [s for s in windowed if s.status == "NU"]

    # Preserve first-seen subject order from the (filtered) dump.
    subject_order: list[str] = []
    display_of: dict[str, str] = {}
    division_of: dict[tuple[str, str], str] = {}
    counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])  # conducted, attended
    nu_by_subject: dict[str, int] = defaultdict(int)

    for slot in windowed:
        if slot.subject not in display_of:
            subject_order.append(slot.subject)
            display_of[slot.subject] = slot.display_name

    for slot in official:
        key = (slot.subject, slot.lecture_type)
        division_of.setdefault(key, slot.course_raw.upper())
        counts[key][0] += 1
        if slot.status in _ATTENDED:
            counts[key][1] += 1

    for slot in pending_nu:
        nu_by_subject[slot.subject] += 1

    courses: list[CourseSummary] = []
    serial = 1
    blockers: list[str] = []
    for subject in subject_order:
        components: list[ComponentRow] = []
        for lecture_type in _COMPONENT_ORDER:
            key = (subject, lecture_type)
            if key not in counts:
                continue
            conducted, attended = counts[key]
            components.append(
                ComponentRow(
                    serial=serial,
                    course_name=display_of[subject],
                    division_name=division_of[key],
                    lecture_type=lecture_type,
                    conducted=conducted,
                    attended=attended,
                )
            )
            serial += 1
        if not components:
            # Subject only had NU hours in the window — skip the official table.
            continue
        held = sum(c.conducted for c in components)
        present = sum(c.attended for c in components)
        pct = _percentage(present, held)
        status = "SAFE" if pct + 1e-12 >= threshold * 100 else "FAILING"
        nu_hours = nu_by_subject.get(subject, 0)
        worst = _percentage(present, held + nu_hours) if nu_hours else pct
        summary = CourseSummary(
            course_name=display_of[subject],
            components=components,
            conducted=held,
            attended=present,
            percentage=pct,
            status=status,
            catch_up_hours=catch_up_hours(present, held, threshold),
            bunks_remaining=bunks_remaining(present, held, threshold),
            nu_hours=nu_hours,
            worst_case_percentage=worst if nu_hours else None,
        )
        courses.append(summary)
        if status == "FAILING":
            blockers.append(summary.course_name)

    windowed_student = Student(
        name=student.name,
        number=student.number,
        roll=student.roll,
        academic_year=student.academic_year,
        academic_session=student.academic_session,
        program=student.program,
        college=student.college,
        report_from=start,
        report_to=end,
    )
    return Report(
        student=windowed_student,
        courses=courses,
        nu_excluded=len(pending_nu),
        exam_blockers=blockers,
        lab_batch=_lab_batch_label(lab_batches),
        threshold=threshold,
        slots_in_window=len(windowed),
        generated_at=dt.now().strftime("%d.%m.%Y %H:%M:%S"),
    )


def catch_up_hours(present: int, held: int, threshold: float = 0.8) -> int:
    """Minimum extra hours that must be attended to reach `threshold`."""
    if held <= 0:
        return 0
    if present / held >= threshold - 1e-12:
        return 0
    return math.ceil((threshold * held - present) / (1.0 - threshold) - 1e-12)


def bunks_remaining(present: int, held: int, threshold: float = 0.8) -> int:
    """Hours that can still be missed at the current held count without going below `threshold`."""
    if held <= 0:
        return 0
    if present / held < threshold - 1e-12:
        return 0
    return max(0, math.floor(present / threshold - held + 1e-12))


def _percentage(present: int, held: int) -> float:
    if held <= 0:
        return 0.0
    return round(100.0 * present / held, 2)


def format_header_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _lab_batch_label(lab_batches: list[str] | None) -> str:
    tags = [b.strip().upper() for b in (lab_batches or []) if b and b.strip()]
    return ",".join(tags) if tags else "all"
