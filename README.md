# attendance-parse

Turn the NMIMS SAP **detailed** attendance PDF (one row per lecture hour) into the **monthly-style** summary PDF the college already issues: one THEO/PRAC row pair per course, combined percentage once, 80% detention gate.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Install (from this directory)

```powershell
uv sync --extra dev
```

## Usage

```powershell
uv run attendance-parse sample_docs\ZSVKM_STUDENT_ATTENDANCE_COPY.pdf -o summary.pdf
uv run attendance-parse report.pdf -o summary.pdf --from 13.07.2026 --to 30.08.2026
uv run attendance-parse report.pdf -o summary.pdf --json summary.json
```

| Flag | Meaning |
|---|---|
| `-o` / `--output` | Summary PDF to write (required) |
| `--json` | Optional JSON sidecar with the same figures |
| `--from` / `--to` | Inclusive window as `dd.MM.yyyy`. Default: the dump's own duration |
| `--lab-batch` | Keep only this batch when a practical row is tagged `J1`/`J2`/… (default `J1`). Unbatched labs always count |
| `--threshold` | Exam-eligibility fraction per course (default `0.8`) |

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
- Practical rows tagged `J2`, `J3`, … are dropped; you are `J1`. Practical rows with no batch tag (whole-class labs) are kept.
- NU hours are listed in a footnote and in the projection block (worst-case if they become Absent). They do not enter the official percentage.

If you are below 80% in a course you must attend `ceil((0.8·held − present) / 0.2)` more hours of that course to climb back. If you are at or above 80%, the projection shows how many hours you can still miss at the **current** held count.

## Samples

- `sample_docs/ZSVKM_STUDENT_ATTENDANCE_COPY.pdf` — detailed dump (input)
- `sample_docs/sample_output.pdf` — college monthly letter (layout we clone)

The monthly letter covers 13.07.2026–30.08.2026. Rebuilding that window from the later detailed dump matches every figure except Linguistics (college 15/18, dump 16/18): one hour was marked Present after the letter was issued.

## Tests

```powershell
uv run pytest
```
