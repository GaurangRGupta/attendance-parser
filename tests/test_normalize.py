from datetime import date

from attendance_parser.extract import extract_document
from attendance_parser.models import RawSlot
from attendance_parser.normalize import PRAC, THEO, display_title, normalize_slots


def _raw(sr: int, course: str, status: str = "P") -> RawSlot:
    return RawSlot(
        sr=sr,
        course_raw=course,
        date=date(2026, 7, 15),
        start="8:00:01 AM",
        end="9:00:00 AM",
        status=status,
    )


def test_title_map_covers_sample_subjects(sample_detailed):
    extracted = extract_document(sample_detailed)
    slots = normalize_slots(extracted.slots)
    names = {s.display_name for s in slots}
    assert "INTRODUCTION TO LINGUISTICS" in names
    assert "SPEECH AND NATURAL LANGUAGE PROCESSING" in names
    assert "ADVANCED DATABASE MANAGEMENT SYSTEMS" in names
    assert "MLOPS" in names


def test_fallback_title_inserts_spaces():
    assert display_title("Introduction toLinguistics") == "INTRODUCTION TO LINGUISTICS"


def test_default_keeps_every_practical_batch():
    rows = [
        _raw(1, "Reinforcement LearningP1-BTDS -J1"),
        _raw(2, "Reinforcement LearningP1-BTDS -J2"),
        _raw(3, "Reinforcement LearningT1-BTDS"),
        _raw(4, "MLOpsP1-BTDS"),
        _raw(5, "Other LabP1-BTDS-A2"),
    ]
    slots = normalize_slots(rows)
    assert [s.sr for s in slots] == [1, 2, 3, 4, 5]
    assert next(s for s in slots if s.sr == 1).batch == "J1"
    assert next(s for s in slots if s.sr == 5).batch == "A2"
    assert next(s for s in slots if s.sr == 4).batch is None


def test_lab_batch_filter_is_not_j_prefixed_and_keeps_unbatched():
    rows = [
        _raw(1, "Reinforcement LearningP1-BTDS -J1"),
        _raw(2, "Reinforcement LearningP1-BTDS -J2"),
        _raw(3, "Reinforcement LearningT1-BTDS"),
        _raw(4, "MLOpsP1-BTDS"),
        _raw(5, "Other LabP1-BTDS-A2"),
    ]
    slots = normalize_slots(rows, lab_batches=["A2"])
    assert [s.sr for s in slots] == [3, 4, 5]
    assert next(s for s in slots if s.sr == 5).lecture_type == PRAC

    slots_j1 = normalize_slots(rows, lab_batches=["J1"])
    assert [s.sr for s in slots_j1] == [1, 3, 4]

    slots_multi = normalize_slots(rows, lab_batches=["j1", "a2"])
    assert [s.sr for s in slots_multi] == [1, 3, 4, 5]


def test_sample_has_seven_subjects_and_linguistics_is_theory_only(sample_detailed):
    slots = normalize_slots(extract_document(sample_detailed).slots)
    by_subject = {}
    for slot in slots:
        by_subject.setdefault(slot.display_name, set()).add(slot.lecture_type)
    assert by_subject["INTRODUCTION TO LINGUISTICS"] == {THEO}
    assert THEO in by_subject["REINFORCEMENT LEARNING"]
    assert PRAC in by_subject["REINFORCEMENT LEARNING"]
    assert len(by_subject) == 7
