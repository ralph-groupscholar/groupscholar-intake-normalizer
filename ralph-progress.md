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

## Iteration 124
- Added readiness scoring and bucket tracking to normalized applications, scorecards, and issue exports.
- Extended Postgres schema + exports to persist readiness metrics and reseeded the production intake batch.
- Refreshed sample outputs and summary report with readiness score statistics.

## Iteration 111
- Added data quality scoring with tiering to the normalization pipeline and exposed scores in JSON, scorecards, and issue exports.
- Extended summary reporting to include data quality averages/ranges plus tier counts for quick triage.
- Updated Postgres schema + exports for data quality metrics and reseeded the production intake_normalizer batch.

## Iteration 63
- Added submission recency tracking across normalized rows, scorecards, summaries, and issues exports.
- Extended Postgres schema and batch/application exports to persist recency buckets and counts.
- Regenerated sample outputs and confirmed test coverage for recency buckets.

## Iteration 66
- Captured email domain categories on each normalized application and summarized them in reports/scorecards.
- Persisted referral sources and email domain categories in the Postgres schema and batch exports.
- Regenerated sample outputs and expanded unit tests for email domain category counts.

## Iteration 67
- Added first-gen participation rates overall and by program to summaries and scorecards.
- Extended batch schema/export to persist first-gen rates and program-level first-gen mix.
- Regenerated sample outputs and expanded tests to cover first-gen rate metrics.

## Iteration 178
- Restored phone capture + normalization with country mix reporting and follow-up flags.
- Extended Postgres schema + exports for phone fields and country mix in batch analytics.
- Refreshed sample intake data, outputs, and tests to cover phone normalization paths.

## Iteration 175
- Added duplicate phone detection with summary/report visibility and follow-up labeling.
- Extended batch schema + exports for duplicate phone counts and refreshed sample outputs.
- Reseeded the production intake_normalizer batch with duplicate phone tracking enabled.

## Iteration 173
- Added graduation year coverage assertions to the summary/scorecard tests.
- Regenerated sample outputs so graduation year sections are present in reports.
- Updated intake field documentation to include referral source and graduation year.
