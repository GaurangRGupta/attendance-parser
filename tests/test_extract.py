from datetime import date

from attendance_parser.extract import extract_document


def test_extract_header_and_row_count(sample_detailed):
    extracted = extract_document(sample_detailed)
    student = extracted.student
    assert student.name
    assert student.number.isdigit()
    assert student.roll
    assert student.academic_year == "2026-2027"
    assert student.academic_session == "Semester VII"
    assert student.program == "B Tech (Data Science)"
    assert student.report_from == date(2026, 6, 1)
    assert student.report_to == date(2026, 9, 18)
    assert len(extracted.slots) == 225
    assert extracted.slots[0].sr == 1
    assert extracted.slots[-1].sr == 225


def test_extract_first_and_last_slots(sample_detailed):
    slots = extract_document(sample_detailed).slots
    first = slots[0]
    assert first.course_raw.startswith("Introduction toLinguistics")
    assert first.status == "P"
    last = slots[-1]
    assert last.status == "NU"
    assert last.date == date(2026, 9, 18)
