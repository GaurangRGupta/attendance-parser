# attendance-parse

Turn the college **detailed** attendance PDF (one row per lecture hour) into the **monthly-style** summary PDF: one THEO/PRAC row pair per course, combined percentage once, 80% detention gate.

Any student on the same portal format can use it with their own dump.

## Requirements

- Windows 10 or 11
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Install

Clone this repository (or copy the folder), then from the project root:

```powershell
.\scripts\install.ps1
```

That creates the virtualenv, installs the package, and puts `attendance-parse` on your PATH via `uv tool install`.

If the command is not found after install, add `%USERPROFILE%\.local\bin` to PATH, or run:

```powershell
uv tool update-shell
```

Then open a new terminal.

In-repo (no global install):

```powershell
uv sync --extra dev
uv run attendance-parse --help
```

## Usage

Export the **detailed** hour-by-hour attendance report from the college portal (not the monthly summary letter). Then:

```powershell
attendance-parse --help
attendance-parse --version
attendance-parse parse .\detailed_dump.pdf -o summary.pdf
attendance-parse parse .\detailed_dump.pdf -o summary.pdf --json summary.json
attendance-parse parse .\detailed_dump.pdf -o summary.pdf --from 13.07.2026 --to 30.08.2026
```

| Flag / command | Meaning |
|---|---|
| `parse` | Read a detailed dump and write the summary PDF |
| `-o` / `--output` | Summary PDF to write (required) |
| `--json` | Optional JSON sidecar with the same figures |
| `--from` / `--to` | Inclusive window as `dd.MM.yyyy`. Default: the dump's own duration |
| `--lab-batch` | Optional, repeatable. If a practical row has a batch tag, keep only tags you list. Tags are the trailing letter+digits code on the course name; they are **not** always `J`-prefixed and can differ by course. Practicals with no tag are always kept. Default: keep every practical row in the dump |
| `--threshold` | Exam-eligibility fraction per course (default `0.8`) |
| `--version` / `version` | Print the version |
| `--help` / `help` | Show help (`help parse` for the parse command) |

Example if you only want certain tagged labs (unbatched labs still count):

```powershell
attendance-parse parse .\detailed_dump.pdf -o summary.pdf --lab-batch A1 --lab-batch B2
```

## How the numbers are counted

Each detailed-PDF row is **one hour**.

| Status | Classes conducted | Classes attended |
|---|---|---|
| P Present | yes | yes |
| A Absent | yes | no |
| E Exemption | yes | yes |
| L Late Admission | no | no |
| NU Not Updated | no | no |

- **Percentage** is per **course**, combining theory + practical hours: attended / conducted. That is what the college monthly letter prints, and what the 80% detention rule uses.
- Practical rows with no batch tag (whole-class labs) always count.
- If you pass `--lab-batch`, tagged practicals whose tag is not in that list are dropped.
- NU hours are listed in a footnote and in the projection block (worst-case if they become Absent). They do not enter the official percentage.

If you are below 80% in a course you must attend `ceil((0.8·held − present) / 0.2)` more hours of that course to climb back. If you are at or above 80%, the projection shows how many hours you can still miss at the **current** held count.

## Tests

```powershell
uv run pytest
```

A personal portal dump is not required. If you keep one locally under `sample_docs/` (gitignored), extra golden tests run against it.

## License

MIT. See `LICENSE`.
