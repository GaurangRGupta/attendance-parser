"""Dataclasses for the detailed dump and the monthly-style summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Student:
    name: str
    number: str
    roll: str
    academic_year: str
    academic_session: str
    program: str
    college: str
    report_from: date
    report_to: date


@dataclass(frozen=True)
class RawSlot:
    """One hour row as extracted from the detailed PDF, before T1/P1 parsing."""

    sr: int
    course_raw: str
    date: date
    start: str
    end: str
    status: str


@dataclass(frozen=True)
class Slot:
    sr: int
    course_raw: str
    date: date
    start: str
    end: str
    status: str
    subject: str
    lecture_type: str  # THEO or PRAC
    batch: str | None
    display_name: str


@dataclass
class ComponentRow:
    serial: int
    course_name: str
    division_name: str
    lecture_type: str
    conducted: int
    attended: int


@dataclass
class Absence:
    """One missed lecture (adjacent A-hours on the same course/day collapsed)."""

    date: date
    course_name: str
    lecture_type: str
    start: str
    end: str
    hours: int


@dataclass
class CourseSummary:
    course_name: str
    components: list[ComponentRow]
    conducted: int
    attended: int
    percentage: float
    status: str  # SAFE or FAILING
    catch_up_hours: int
    bunks_remaining: int
    nu_hours: int
    worst_case_percentage: float | None


@dataclass
class Report:
    student: Student
    courses: list[CourseSummary]
    nu_excluded: int
    exam_blockers: list[str]
    lab_batch: str
    threshold: float
    slots_in_window: int
    absences: list[Absence] = field(default_factory=list)
    generated_at: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    student: Student
    slots: list[RawSlot]
