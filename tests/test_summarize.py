from datetime import date

from attendance_parser.pipeline import build_report
from attendance_parser.summarize import bunks_remaining, catch_up_hours


def _by_name(report):
    return {c.course_name: c for c in report.courses}


def _comp(course, lecture_type):
    return next(c for c in course.components if c.lecture_type == lecture_type)


def test_catch_up_and_bunk_formulas():
    assert catch_up_hours(18, 26) == 14
    assert catch_up_hours(14, 18) == 2
    assert catch_up_hours(26, 32) == 0
    assert bunks_remaining(36, 36) == 9
    assert bunks_remaining(30, 30) == 7
    assert bunks_remaining(26, 32) == 0
    assert bunks_remaining(18, 26) == 0


def test_full_dump_golden_counts(sample_detailed):
    report = build_report(sample_detailed)
    courses = _by_name(report)
    assert report.nu_excluded == 13
    assert report.exam_blockers == ["INTRODUCTION TO LINGUISTICS"]

    ling = courses["INTRODUCTION TO LINGUISTICS"]
    assert len(ling.components) == 1
    assert _comp(ling, "THEO").conducted == 26
    assert _comp(ling, "THEO").attended == 18
    assert ling.percentage == 69.23
    assert ling.status == "FAILING"
    assert ling.catch_up_hours == 14
    assert ling.nu_hours == 3
    assert ling.worst_case_percentage == 62.07

    rl = courses["REINFORCEMENT LEARNING"]
    assert _comp(rl, "PRAC").conducted == 18
    assert _comp(rl, "PRAC").attended == 14
    assert _comp(rl, "THEO").conducted == 14
    assert _comp(rl, "THEO").attended == 12
    assert rl.percentage == 81.25
    assert rl.status == "SAFE"
    assert rl.bunks_remaining == 0
    assert rl.nu_hours == 4
    assert rl.worst_case_percentage == 72.22

    adms = courses["ADVANCED DATABASE MANAGEMENT SYSTEMS"]
    assert _comp(adms, "PRAC").conducted == 18
    assert _comp(adms, "THEO").conducted == 18
    assert adms.percentage == 100.0
    assert adms.bunks_remaining == 9

    mlops = courses["MLOPS"]
    assert mlops.attended == 30
    assert mlops.conducted == 30
    assert mlops.nu_hours == 2


def test_monthly_window_matches_college_except_linguistics_backfill(sample_detailed):
    """College monthly PDF is 13.07.2026–30.08.2026.

    Every conducted/attended figure matches except Linguistics (college 15/18,
    this later dump 16/18) — one hour was marked Present after the monthly
    letter was issued.
    """
    report = build_report(
        sample_detailed,
        date_from=date(2026, 7, 13),
        date_to=date(2026, 8, 30),
    )
    courses = _by_name(report)
    assert report.nu_excluded == 0

    adms = courses["ADVANCED DATABASE MANAGEMENT SYSTEMS"]
    assert (_comp(adms, "PRAC").conducted, _comp(adms, "PRAC").attended) == (14, 14)
    assert (_comp(adms, "THEO").conducted, _comp(adms, "THEO").attended) == (13, 13)
    assert adms.percentage == 100.0

    rl = courses["REINFORCEMENT LEARNING"]
    assert (_comp(rl, "PRAC").conducted, _comp(rl, "PRAC").attended) == (14, 12)
    assert (_comp(rl, "THEO").conducted, _comp(rl, "THEO").attended) == (12, 12)
    assert rl.percentage == 92.31

    nndl = courses["NEURAL NETWORKS AND DEEP LEARNING"]
    assert nndl.percentage == 100.0
    assert _comp(nndl, "THEO").conducted == 12
    assert _comp(nndl, "PRAC").conducted == 12

    snlp = courses["SPEECH AND NATURAL LANGUAGE PROCESSING"]
    assert _comp(snlp, "THEO").conducted == 12
    assert _comp(snlp, "PRAC").conducted == 12

    bda = courses["BIG DATA ANALYTICS"]
    assert _comp(bda, "THEO").conducted == 14
    assert _comp(bda, "PRAC").conducted == 14

    mlops = courses["MLOPS"]
    assert _comp(mlops, "THEO").conducted == 14
    assert _comp(mlops, "PRAC").conducted == 14

    ling = courses["INTRODUCTION TO LINGUISTICS"]
    assert (_comp(ling, "THEO").conducted, _comp(ling, "THEO").attended) == (18, 16)
    assert ling.percentage == 88.89
