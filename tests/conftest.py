from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DETAILED = ROOT / "sample_docs" / "ZSVKM_STUDENT_ATTENDANCE_COPY.pdf"
SAMPLE_MONTHLY = ROOT / "sample_docs" / "sample_output.pdf"


@pytest.fixture
def sample_detailed() -> Path:
    assert SAMPLE_DETAILED.is_file(), f"missing {SAMPLE_DETAILED}"
    return SAMPLE_DETAILED
