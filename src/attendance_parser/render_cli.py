"""Short terminal echo of the summary (the PDF is the artefact)."""

from __future__ import annotations

from attendance_parser.models import Report
from attendance_parser.summarize import format_header_date


def render_cli(report: Report, pdf_path: str) -> str:
    student = report.student
    lines = [
        f"{student.name}  |  {student.roll}  |  {student.program}",
        f"{student.academic_year}, {student.academic_session}"
        f"  |  {format_header_date(student.report_from)}–{format_header_date(student.report_to)}"
        f"  |  lab batch {report.lab_batch}  |  {report.threshold:.0%} gate",
        f"{report.slots_in_window} slots in window  |  {report.nu_excluded} NU excluded",
        "",
        f"{'Course':<42} {'Type':<6} {'Att/Cond':<10} {'Course %':<10} {'Status'}",
        "-" * 86,
    ]
    for course in report.courses:
        for i, comp in enumerate(course.components):
            pct = f"{course.percentage:.2f}%" if i == 0 else ""
            status = course.status if i == 0 else ""
            lines.append(
                f"{comp.course_name:<42} {comp.lecture_type:<6} "
                f"{comp.attended}/{comp.conducted:<7} {pct:<10} {status}"
            )
    lines.append("")
    if report.exam_blockers:
        lines.append("EXAM BLOCKERS: " + ", ".join(report.exam_blockers))
    else:
        lines.append("EXAM BLOCKERS: none")
    lines.append("")
    lines.append(render_absences(report))
    lines.append(f"Wrote {pdf_path}")
    return "\n".join(lines)


def render_absences(report: Report) -> str:
    if not report.absences:
        return "Absences: none"
    lines = [
        f"Absences ({len(report.absences)} lecture(s)):",
        f"{'Date':<12} {'Course':<42} {'Type':<6} {'Time':<13} Hours",
        "-" * 80,
    ]
    for item in report.absences:
        time_span = f"{item.start}–{item.end}"
        lines.append(
            f"{format_header_date(item.date):<12} {item.course_name:<42} "
            f"{item.lecture_type:<6} {time_span:<13} {item.hours}"
        )
    return "\n".join(lines)
