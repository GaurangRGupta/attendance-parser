import json

from typer.testing import CliRunner

from attendance_parser import __version__
from attendance_parser.cli import app

runner = CliRunner()


def test_help_and_version_need_no_pdf():
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "parse" in help_result.output
    assert "version" in help_result.output

    none = runner.invoke(app, [])
    assert "parse" in none.output

    flag = runner.invoke(app, ["--version"])
    assert flag.exit_code == 0, flag.output
    assert __version__ in flag.output

    sub = runner.invoke(app, ["version"])
    assert sub.exit_code == 0, sub.output
    assert __version__ in sub.output

    help_sub = runner.invoke(app, ["help"])
    assert help_sub.exit_code == 0, help_sub.output
    assert "parse" in help_sub.output

    help_parse = runner.invoke(app, ["help", "parse"])
    assert help_parse.exit_code == 0, help_parse.output
    assert "--output" in help_parse.output or "-o" in help_parse.output
    assert "attendance-parse parse" in help_parse.output


def test_cli_writes_pdf_and_json(sample_detailed, tmp_path):
    pdf_out = tmp_path / "summary.pdf"
    json_out = tmp_path / "summary.json"
    result = runner.invoke(
        app,
        [
            "parse",
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
            "parse",
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
        ["parse", str(sample_detailed), "-o", str(tmp_path / "x.pdf"), "--from", "2026-07-13"],
    )
    assert result.exit_code == 2


def test_cli_parse_synthetic(synthetic_detailed, tmp_path):
    pdf_out = tmp_path / "out.pdf"
    json_out = tmp_path / "out.json"
    result = runner.invoke(
        app,
        ["parse", str(synthetic_detailed), "-o", str(pdf_out), "--json", str(json_out)],
    )
    assert result.exit_code == 0, result.output
    assert pdf_out.is_file()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["student"]["name"] == "TEST STUDENT"
    assert payload["student"]["number"] == "00000000000"
    names = {c["course_name"]: c for c in payload["courses"]}
    assert "SAMPLE COURSE ALPHA" in names
    assert "SAMPLE COURSE BETA" in names
    # Unfiltered: A1 and B2 practical hours both count on Alpha.
    alpha_prac = next(c for c in names["SAMPLE COURSE ALPHA"]["components"] if c["lecture_type"] == "PRAC")
    assert alpha_prac["conducted"] == 2

    filtered = runner.invoke(
        app,
        [
            "parse",
            str(synthetic_detailed),
            "-o",
            str(tmp_path / "filtered.pdf"),
            "--json",
            str(tmp_path / "filtered.json"),
            "--lab-batch",
            "A1",
        ],
    )
    assert filtered.exit_code == 0, filtered.output
    payload2 = json.loads((tmp_path / "filtered.json").read_text(encoding="utf-8"))
    names2 = {c["course_name"]: c for c in payload2["courses"]}
    alpha_prac2 = next(c for c in names2["SAMPLE COURSE ALPHA"]["components"] if c["lecture_type"] == "PRAC")
    assert alpha_prac2["conducted"] == 1
    beta_prac = next(c for c in names2["SAMPLE COURSE BETA"]["components"] if c["lecture_type"] == "PRAC")
    assert beta_prac["conducted"] == 1
