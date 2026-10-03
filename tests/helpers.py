"""Build a tiny fake detailed-attendance PDF for tests (no personal data)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def write_synthetic_detailed_pdf(path: Path) -> Path:
    """Write a 7-row dump: tagged labs A1/B2, unbatched lab, theory, NU, two adjacent A hours."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    style = ParagraphStyle("body", fontName="Times-Roman", fontSize=10, leading=12)
    header = [
        Paragraph("SVKM'S NMIMS Mukesh Patel Schl of Tech Mgt & Engg-Mum, Mumbai", style),
        Spacer(1, 6),
        Paragraph("Student Name TEST STUDENT", style),
        Paragraph("Student Number 00000000000", style),
        Paragraph("Roll No. T001", style),
        Paragraph("Academic Year & Academic Session 2026-2027, Semester VII", style),
        Paragraph("Program Name B Tech (Data Science)", style),
        Paragraph("Attendance Report Duration : From 01.07.2026 to 31.07.2026", style),
        Spacer(1, 10),
    ]
    rows = [
        ["Sr No.", "Course Name", "Date", "Start Time", "End Time", "Attendance"],
        ["1", "Sample Course AlphaP1-BTDS-A1", "Jul 15, 2026", "8:00:01 AM", "9:00:00 AM", "P"],
        ["2", "Sample Course AlphaP1-BTDS-B2", "Jul 15, 2026", "9:00:01 AM", "10:00:00 AM", "P"],
        ["3", "Sample Course AlphaT1-BTDS", "Jul 16, 2026", "10:00:01 AM", "11:00:00 AM", "A"],
        ["4", "Sample Course BetaP1-BTDS", "Jul 16, 2026", "11:00:01 AM", "12:00:00 PM", "P"],
        ["5", "Sample Course BetaT1-BTDS", "Jul 17, 2026", "9:00:01 AM", "10:00:00 AM", "NU"],
        ["6", "Sample Course GammaT1-BTDS", "Jul 18, 2026", "2:00:01 PM", "3:00:00 PM", "A"],
        ["7", "Sample Course GammaT1-BTDS", "Jul 18, 2026", "3:00:01 PM", "4:00:00 PM", "A"],
    ]
    table = Table(rows, colWidths=[20 * mm, 55 * mm, 35 * mm, 30 * mm, 30 * mm, 22 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    SimpleDocTemplate(str(path), pagesize=A4).build(header + [table])
    return path
