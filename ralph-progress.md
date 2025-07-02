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
