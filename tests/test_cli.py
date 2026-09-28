import json

from typer.testing import CliRunner

from attendance_parser.cli import app

runner = CliRunner()


def test_cli_writes_pdf_and_json(sample_detailed, tmp_path):
    pdf_out = tmp_path / "summary.pdf"
    json_out = tmp_path / "summary.json"
    result = runner.invoke(
        app,
        [
            str(sample_detailed),
            "-o",
            str(pdf_out),
            "--json",
            str(json_out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert pdf_out.is_file()
    assert json_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    courses = {c["course_name"]: c for c in payload["courses"]}
    assert courses["INTRODUCTION TO LINGUISTICS"]["percentage"] == 69.23
    assert courses["REINFORCEMENT LEARNING"]["percentage"] == 81.25
    assert payload["exam_blockers"] == ["INTRODUCTION TO LINGUISTICS"]
    assert "Wrote" in result.output
    assert "FAILING" in result.output


def test_cli_monthly_window(sample_detailed, tmp_path):
    pdf_out = tmp_path / "monthly.pdf"
    json_out = tmp_path / "monthly.json"
    result = runner.invoke(
        app,
        [
            str(sample_detailed),
            "-o",
            str(pdf_out),
            "--json",
            str(json_out),
            "--from",
            "13.07.2026",
            "--to",
            "30.08.2026",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    courses = {c["course_name"]: c for c in payload["courses"]}
    assert courses["REINFORCEMENT LEARNING"]["percentage"] == 92.31
    assert payload["nu_excluded"] == 0


def test_cli_bad_date(sample_detailed, tmp_path):
    result = runner.invoke(
        app,
        [str(sample_detailed), "-o", str(tmp_path / "x.pdf"), "--from", "2026-07-13"],
    )
    assert result.exit_code == 2
