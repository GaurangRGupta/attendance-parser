import pdfplumber

from attendance_parser.pipeline import build_report
from attendance_parser.render_pdf import LETTERHEAD, render_pdf


def test_rendered_pdf_contains_college_layout_and_figures(sample_detailed, tmp_path):
    report = build_report(sample_detailed)
    out = tmp_path / "summary.pdf"
    render_pdf(report, out)
    assert out.is_file()

    with pdfplumber.open(out) as doc:
        assert len(doc.pages) >= 1
        text = "\n".join(page.extract_text() or "" for page in doc.pages)

    collapsed = " ".join(text.split())
    assert LETTERHEAD in collapsed
    assert report.student.name in text
    assert report.student.roll in text
    assert "INTRODUCTION TO LINGUISTICS" in text
    assert "69.23" in text
    assert "81.25" in text
    assert "EXAM BLOCKERS" in text
    assert "80% attendance in each course" in text
    assert "NU (Not Updated)" in text

    # Combined % sits in the table; Linguistics is theory-only so 69.23 appears once.
    assert text.count("69.23") >= 1
    assert "Absent lectures" in text


def test_rendered_pdf_lists_synthetic_absences(synthetic_detailed, tmp_path):
    report = build_report(synthetic_detailed)
    out = tmp_path / "summary.pdf"
    render_pdf(report, out)
    with pdfplumber.open(out) as doc:
        text = "\n".join(page.extract_text() or "" for page in doc.pages)
    assert "SAMPLE COURSE GAMMA" in text
    assert "14:00" in text
    assert "Absences: none" not in text
