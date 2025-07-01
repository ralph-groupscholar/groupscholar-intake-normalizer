# Group Scholar Intake Normalizer

Normalize scholarship intake CSV files into a consistent JSON payload with lightweight quality flags and an executive-ready summary report. Designed for local-first, offline workflows using Python's standard library.

## What it does

- Parses an intake CSV and standardizes fields (dates, program names, booleans).
- Normalizes column headers (common aliases) to reduce prep work.
- Generates a normalized JSON dataset for downstream dashboards.
- Produces a summary report with risk flags, submission window, and duplicate email counts.

## Quick start

```bash
python3 src/normalizer.py --input data/sample_applications.csv --out output/normalized.json --report output/summary.md
```

## Output

- `output/normalized.json` with normalized rows + computed flags.
- `output/summary.md` with a one-page intake snapshot.

## Fields (input)

Expected columns in the intake CSV:

- applicant_id
- name
- email
- program
- gpa
- income_bracket
- submission_date
- first_gen
- eligibility_notes

Common header aliases are supported (e.g., "Applicant ID", "Email Address",
"Submission Date") and are normalized automatically.

## Notes

- Uses only the Python standard library.
- Defaults are conservative and transparent for review teams.
