# Group Scholar Intake Normalizer

Normalize scholarship intake CSV files into a consistent JSON payload with lightweight quality flags and an executive-ready summary report. Designed for local-first, offline workflows using Python's standard library.

## What it does

- Parses an intake CSV and standardizes fields (dates, program names, booleans).
- Normalizes column headers (common aliases) to reduce prep work.
- Generates a normalized JSON dataset for downstream dashboards.
- Produces a summary report with risk flags, GPA stats, submission window, and duplicate counts.
- Optional scorecard JSON for downstream QA automation.
- Flags missing programs and out-of-range GPAs for follow-up.

## Quick start

```bash
python3 src/normalizer.py \
  --input data/sample_applications.csv \
  --out output/normalized.json \
  --report output/summary.md \
  --issues output/issues.csv \
  --scorecard output/scorecard.json
```

## Database export

Export each normalization run into the shared Group Scholar Postgres cluster.

```bash
python3 -m pip install -r requirements.txt
export GROUPSCHOLAR_INTAKE_DB_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
python3 src/normalizer.py \
  --input data/sample_applications.csv \
  --out output/normalized.json \
  --report output/summary.md \
  --issues output/issues.csv \
  --scorecard output/scorecard.json \
  --db \
  --batch-label "Sample intake"
```

- The schema lives in `db/schema.sql` under `intake_normalizer`.
- Each run creates a batch record and associated applications.

## Output

- `output/normalized.json` with normalized rows + computed flags.
- `output/summary.md` with a one-page intake snapshot.
- `output/issues.csv` with only the applications that need follow-up.
- `output/scorecard.json` with rates + aggregates for QA dashboards.

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

- Uses only the Python standard library unless you opt into Postgres export.
- Defaults are conservative and transparent for review teams.
