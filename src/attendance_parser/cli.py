"""Command-line interface: detailed SAP dump in, monthly-style PDF out."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click
import typer

from attendance_parser import __version__
from attendance_parser.errors import AttendanceError
from attendance_parser.json_out import write_json
from attendance_parser.pipeline import build_report
from attendance_parser.models import Report
from attendance_parser.render_cli import render_absences, render_cli
from attendance_parser.render_pdf import render_pdf

app = typer.Typer(
    name="attendance-parse",
    help="Build a monthly-style attendance summary PDF from a detailed SAP dump.",
    add_completion=False,
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"attendance-parse {__version__}")
        raise typer.Exit()


def _load_report(
    pdf: Path,
    date_from: str | None,
    date_to: str | None,
    lab_batch: list[str],
    threshold: float = 0.8,
) -> Report:
    return build_report(
        pdf,
        lab_batches=lab_batch or None,
        date_from=_parse_cli_date(date_from, "--from"),
        date_to=_parse_cli_date(date_to, "--to"),
        threshold=threshold,
    )


def _parse_cli_date(value: str | None, flag: str):
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        typer.echo(f"{flag} must be dd.MM.yyyy (got {value!r}).", err=True)
        raise typer.Exit(code=2)


@app.callback()
def _root(
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


@app.command()
def version() -> None:
    """Show the version and exit."""
    typer.echo(f"attendance-parse {__version__}")


@app.command("help")
def help_command(
    ctx: typer.Context,
    command_name: str | None = typer.Argument(
        None,
        help="Subcommand to describe (parse, absences, version, help).",
    ),
) -> None:
    """Show help for the application or a specific command."""
    parent_ctx = ctx.parent or ctx
    group = parent_ctx.command
    if command_name is None:
        typer.echo(group.get_help(parent_ctx))
        return
    sub = group.get_command(parent_ctx, command_name)
    if sub is None:
        typer.echo(f"Unknown command: {command_name}", err=True)
        raise typer.Exit(code=2)
    with click.Context(sub, info_name=command_name, parent=parent_ctx) as sub_ctx:
        typer.echo(sub.get_help(sub_ctx))


@app.command()
def parse(
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
    lab_batch: list[str] = typer.Option(
        [],
        "--lab-batch",
        help=(
            "If a practical row has a batch tag, keep it only when the tag is one of these "
            "(repeatable). Tags are the trailing letter+digits code on the course name; they "
            "are not always J-prefixed and can differ by course. Practicals with no tag are "
            "always kept. Default: keep every practical row in the dump."
        ),
    ),
    threshold: float = typer.Option(
        0.8,
        "--threshold",
        help="Exam-eligibility fraction per course (combined theory + practical).",
    ),
) -> None:
    """Parse a detailed dump and write a monthly-style summary PDF."""
    try:
        report = _load_report(pdf, date_from, date_to, lab_batch, threshold)
        written = render_pdf(report, output)
        if json_path is not None:
            write_json(report, json_path)
    except AttendanceError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(render_cli(report, str(written)))


@app.command()
def absences(
    pdf: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        show_default=False,
        help="Detailed SAP attendance PDF (one row per lecture hour).",
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
    lab_batch: list[str] = typer.Option(
        [],
        "--lab-batch",
        help=(
            "If a practical row has a batch tag, keep it only when the tag is one of these "
            "(repeatable). Practicals with no tag are always kept. Default: keep every "
            "practical row in the dump."
        ),
    ),
) -> None:
    """List lectures marked Absent (A). Adjacent hours on the same day are grouped."""
    try:
        report = _load_report(pdf, date_from, date_to, lab_batch)
    except AttendanceError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(render_absences(report))
