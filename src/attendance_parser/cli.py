"""Command-line interface: detailed SAP dump in, monthly-style PDF out."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer

from attendance_parser import __version__
from attendance_parser.errors import AttendanceError
from attendance_parser.json_out import write_json
from attendance_parser.pipeline import build_report
from attendance_parser.render_cli import render_cli
from attendance_parser.render_pdf import render_pdf

app = typer.Typer(
    name="attendance-parse",
    help="Build a monthly-style attendance summary PDF from a detailed SAP dump.",
    add_completion=False,
    pretty_exceptions_show_locals=False,
    invoke_without_command=True,
    no_args_is_help=True,
    context_settings={"allow_interspersed_args": True},
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"attendance-parse {__version__}")
        raise typer.Exit()


def _parse_cli_date(value: str | None, flag: str):
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        typer.echo(f"{flag} must be dd.MM.yyyy (got {value!r}).", err=True)
        raise typer.Exit(code=2)


@app.callback()
def main(
    pdf: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        show_default=False,
        help="Detailed SAP attendance PDF (one row per lecture hour).",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Monthly-style summary PDF to write.",
        show_default=False,
    ),
    json_path: Path | None = typer.Option(
        None,
        "--json",
        help="Optional JSON sidecar with the same figures.",
    ),
    date_from: str | None = typer.Option(
        None,
        "--from",
        help="Inclusive start date (dd.MM.yyyy). Default: duration on the dump.",
    ),
    date_to: str | None = typer.Option(
        None,
        "--to",
        help="Inclusive end date (dd.MM.yyyy). Default: duration on the dump.",
    ),
    lab_batch: str = typer.Option(
        "J1",
        "--lab-batch",
        help="Keep only this lab batch when a P-row is tagged J1/J2/… Unbatched labs are always kept.",
    ),
    threshold: float = typer.Option(
        0.8,
        "--threshold",
        help="Exam-eligibility fraction per course (combined theory + practical).",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the version and exit.",
        callback=_show_version,
        is_eager=True,
    ),
) -> None:
    """Build a monthly-style attendance summary PDF from a detailed SAP dump."""
    try:
        report = build_report(
            pdf,
            lab_batch=lab_batch,
            date_from=_parse_cli_date(date_from, "--from"),
            date_to=_parse_cli_date(date_to, "--to"),
            threshold=threshold,
        )
        written = render_pdf(report, output)
        if json_path is not None:
            write_json(report, json_path)
    except AttendanceError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(render_cli(report, str(written)))
