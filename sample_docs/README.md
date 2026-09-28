# Local attendance dumps

Put the **detailed** hour-by-hour attendance PDF from the college portal in this folder if you want a local copy. Do not commit it.

That report is one row per lecture hour (course name, date, start/end, P/A/NU). It is not the monthly summary letter.

The portal file contains student identity and attendance. It is gitignored on purpose.

```powershell
attendance-parse parse .\your_detailed_report.pdf -o summary.pdf
```

If a practical row is tagged with a batch that is not yours, pass `--lab-batch` once per tag you want to keep (see the project README). Unbatched practicals are always kept. The dump is usually already limited to your own sessions, so the flag is optional.
