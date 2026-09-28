"""Write a monthly-style summary PDF cloned from the college layout."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from attendance_parser.models import Report
from attendance_parser.summarize import format_header_date

LETTERHEAD = "MUKESH PATEL SCHOOL OF TECHNOLOGY MANAGEMENT & ENGINEERING - MUMBAI"

_COLLEGE_NOTES = [
    (
        "1. The overall attendance % for each course is reflected once, whereas lectures "
        "conducted/attended for Theory / Practical/Tutorial/Studio are shown in a separate "
        "row, as applicable."
    ),
    (
        "2. Please contact school Course Co-ordinator/AR/DR for any attendance-related "
        "queries within 2 days from the receipt of the report."
    ),
    (
        "3. You will be detained if you do not comply with the attendance requirement of "
        "80% attendance in each course. You have to register afresh and repeat the "
        "Semester / Year in the subsequent Academic year as per readmission rules "
        "mentioned in the Student Resource Book."
    ),
    (
        "4. For academic-related concerns, please write to us at "
        "mpstme-mum.academics@nmims.edu with the following details to ensure prompt "
        "assistance."
    ),
    "Student SAP ID | Student Name | Student Roll No. | Name of the Program | Academic Term",
]


def render_pdf(report: Report, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = _styles()
    story: list = [
        Paragraph(_esc(LETTERHEAD), styles["letterhead"]),
        Spacer(1, 10),
        _meta_table(report, styles),
        Spacer(1, 14),
        Paragraph(
            _esc(
                f"Attendance Report Date: From {format_header_date(report.student.report_from)}"
                f" To {format_header_date(report.student.report_to)}"
            ),
            styles["body"],
        ),
        Spacer(1, 10),
        _attendance_table(report, styles),
        Spacer(1, 12),
    ]
    for note in _COLLEGE_NOTES:
        story.append(Paragraph(_esc(note), styles["note"]))
        story.append(Spacer(1, 4))

    if report.nu_excluded:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                _esc(
                    f"5. {report.nu_excluded} hour(s) marked NU (Not Updated) were excluded "
                    "from classes conducted/attended. They are not in the official percentage."
                ),
                styles["note"],
            )
        )

    story.append(Spacer(1, 12))
    story.append(_projection_block(report, styles))

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title=f"Attendance summary — {report.student.name}",
        author="attendance-parse",
    )
    generated = report.generated_at
    doc.build(
        story,
        onFirstPage=lambda c, d: _footer(c, d, generated),
        onLaterPages=lambda c, d: _footer(c, d, generated),
    )
    return output


def _styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName="Times-Roman", fontSize=11, leading=14)
    return {
        "letterhead": ParagraphStyle(
            "letterhead",
            fontName="Times-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "body": ParagraphStyle("body", alignment=TA_LEFT, **base),
        "meta_label": ParagraphStyle("meta_label", fontName="Times-Roman", fontSize=11, leading=14),
        "meta_value": ParagraphStyle("meta_value", fontName="Times-Roman", fontSize=11, leading=14),
        "th": ParagraphStyle(
            "th",
            fontName="Times-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
        "td": ParagraphStyle("td", fontName="Times-Roman", fontSize=9, leading=11, alignment=TA_LEFT),
        "tdc": ParagraphStyle(
            "tdc",
            fontName="Times-Roman",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
        "pct": ParagraphStyle(
            "pct",
            fontName="Times-Bold",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle("note", alignment=TA_JUSTIFY, fontSize=9, leading=12, **{"fontName": "Times-Roman"}),
        "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=11, leading=14, spaceAfter=6),
        "proj_th": ParagraphStyle(
            "proj_th",
            fontName="Times-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
        "proj_td": ParagraphStyle("proj_td", fontName="Times-Roman", fontSize=9, leading=11),
        "proj_tdc": ParagraphStyle(
            "proj_tdc",
            fontName="Times-Roman",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
    }


def _meta_table(report: Report, styles: dict[str, ParagraphStyle]) -> Table:
    student = report.student
    session = ", ".join(p for p in (student.academic_year, student.academic_session) if p)
    rows = [
        [_p("Student Name:", styles["meta_label"]), _p(student.name, styles["meta_value"])],
        [_p("Student Number:", styles["meta_label"]), _p(student.number, styles["meta_value"])],
        [_p("Additional ID Number:", styles["meta_label"]), _p(student.roll, styles["meta_value"])],
        [_p("Academic Year & Academic Session", styles["meta_label"]), _p(session, styles["meta_value"])],
        [_p("Program Name:", styles["meta_label"]), _p(student.program, styles["meta_value"])],
    ]
    table = Table(rows, colWidths=[70 * mm, 110 * mm])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _attendance_table(report: Report, styles: dict[str, ParagraphStyle]) -> Table:
    header = [
        _p("S.No.", styles["th"]),
        _p("Course Name", styles["th"]),
        _p("Division Name", styles["th"]),
        _p("Lecture Type", styles["th"]),
        _p("Total No. Of Classes Conducted", styles["th"]),
        _p("Total No. Of Classes Attended", styles["th"]),
        _p("Percentage (%)", styles["th"]),
    ]
    data = [header]
    spans: list[tuple[int, int]] = []
    row_idx = 1
    for course in report.courses:
        n = len(course.components)
        for i, comp in enumerate(course.components):
            pct_cell = _p(f"{course.percentage:.2f}", styles["pct"]) if i == 0 else _p("", styles["pct"])
            data.append(
                [
                    _p(str(comp.serial), styles["tdc"]),
                    _p(comp.course_name, styles["td"]),
                    _p(comp.division_name, styles["td"]),
                    _p(comp.lecture_type, styles["tdc"]),
                    _p(str(comp.conducted), styles["tdc"]),
                    _p(str(comp.attended), styles["tdc"]),
                    pct_cell,
                ]
            )
        if n > 1:
            spans.append((row_idx, row_idx + n - 1))
        row_idx += n

    usable = A4[0] - 24 * mm
    col_widths = [
        0.06 * usable,
        0.20 * usable,
        0.26 * usable,
        0.08 * usable,
        0.13 * usable,
        0.13 * usable,
        0.14 * usable,
    ]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for start, end in spans:
        style_cmds.append(("SPAN", (6, start), (6, end)))
        style_cmds.append(("VALIGN", (6, start), (6, end), "MIDDLE"))
    table.setStyle(TableStyle(style_cmds))
    return table


def _projection_block(report: Report, styles: dict[str, ParagraphStyle]):
    header = [
        _p("Course", styles["proj_th"]),
        _p("Official %", styles["proj_th"]),
        _p("vs 80%", styles["proj_th"]),
        _p("Projection", styles["proj_th"]),
    ]
    rows = [header]
    for course in report.courses:
        rows.append(
            [
                _p(course.course_name, styles["proj_td"]),
                _p(f"{course.percentage:.2f}", styles["proj_tdc"]),
                _p(course.status, styles["proj_tdc"]),
                _p(_projection_text(course, report.threshold), styles["proj_td"]),
            ]
        )
    usable = A4[0] - 24 * mm
    table = Table(rows, colWidths=[0.38 * usable, 0.14 * usable, 0.12 * usable, 0.36 * usable], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    title = Paragraph(_esc("Projection vs 80% (per course, combined theory + practical)"), styles["h2"])
    blockers = (
        Paragraph(
            _esc("EXAM BLOCKERS: " + ", ".join(report.exam_blockers)),
            styles["body"],
        )
        if report.exam_blockers
        else Paragraph(_esc("EXAM BLOCKERS: none - every course is at or above 80%."), styles["body"])
    )
    return KeepTogether([title, table, Spacer(1, 8), blockers])


def _projection_text(course, threshold: float) -> str:
    bits: list[str] = []
    if course.status == "FAILING":
        bits.append(f"attend at least {course.catch_up_hours} more hour(s) to reach {threshold:.0%}")
    elif course.bunks_remaining == 0:
        bits.append("cannot miss any more hours at the current held count")
    else:
        bits.append(f"can miss {course.bunks_remaining} more hour(s) at the current held count")
    if course.nu_hours and course.worst_case_percentage is not None:
        bits.append(
            f"worst-case if {course.nu_hours} NU hour(s) become Absent: {course.worst_case_percentage:.2f}%"
        )
    return "; ".join(bits)


def _footer(canvas, doc, generated_at: str) -> None:
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    y = 12 * mm
    canvas.drawString(
        doc.leftMargin,
        y + 10,
        "This is system generated attendance report and needs no signature....",
    )
    if generated_at:
        canvas.drawString(doc.leftMargin, y, generated_at)
    canvas.restoreState()


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_esc(text), style)


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
