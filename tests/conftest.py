from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DETAILED = ROOT / "sample_docs" / "ZSVKM_STUDENT_ATTENDANCE_COPY.pdf"


@pytest.fixture
def sample_detailed() -> Path:
    if not SAMPLE_DETAILED.is_file():
        pytest.skip("local detailed dump not present (gitignored personal PDF)")
    return SAMPLE_DETAILED


@pytest.fixture
def synthetic_detailed(tmp_path) -> Path:
    from helpers import write_synthetic_detailed_pdf

    return write_synthetic_detailed_pdf(tmp_path / "synthetic_detailed.pdf")
