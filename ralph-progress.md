# Group Scholar Intake Normalizer Progress

## Iteration 1
- Established the Python CLI normalizer skeleton.
- Added sample intake CSV data plus JSON and summary report outputs.
- Documented usage and expected input fields.

## Iteration 2
- Added header alias normalization to reduce intake prep work.
- Expanded quality flags (invalid email/GPA, future dates, missing IDs).
- Enhanced summary reporting with duplicate email and submission window stats.

## Iteration 3
- Added missing-name and duplicate applicant ID detection, with per-application duplicate flags.
- Generated an optional issues CSV output to surface follow-up needs with friendly reasons.
- Refreshed sample data and outputs to showcase new summary metrics and issue tracking.

## Iteration 30
- Added missing-program and GPA out-of-range validation with new summary metrics.
- Updated database schema + batch export to store the new quality indicators.
- Refreshed sample intake data and regenerated output artifacts with new flags.

## Iteration 4
- Moved shared data models into a dedicated module and aligned Postgres export imports.
- Hardened schema initialization to apply multi-statement migrations reliably.
- Seeded the production intake_normalizer tables with the latest sample intake batch.

## Iteration 4
- Normalized income brackets into standard bands and added income mix reporting to summaries/scorecards.
- Stored income bracket counts in Postgres batch exports and refreshed sample outputs.
- Fixed model coverage for summary fields to align with export payloads.

## Iteration 5
- Ran the Postgres seed export for the latest sample intake batch to refresh production data.
- Verified the schema migration script applies cleanly with multi-statement execution.

## Iteration 6
- Refreshed the production intake_normalizer batch with the latest review readiness outputs.
- Regenerated sample reports, scorecards, and issue lists after the readiness refresh.

## Iteration 6
- Added eligibility note tag extraction with summary/scorecard counts and per-application tags.
- Extended Postgres schema + exports to persist note tags and batch tag counts.
- Regenerated sample outputs and seeded the production intake_normalizer tables with the updated batch.

## Iteration 79
- Added review priority counts to the summary report and scorecard outputs plus review status in issues export.
- Updated Postgres schema and indexes to support review status/priority analytics and reseeded the production batch.
- Regenerated sample outputs to reflect review readiness and priority metrics.
