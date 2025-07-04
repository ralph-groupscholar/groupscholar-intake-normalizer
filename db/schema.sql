CREATE SCHEMA IF NOT EXISTS intake_normalizer;

CREATE TABLE IF NOT EXISTS intake_normalizer.batches (
  batch_id UUID PRIMARY KEY,
  batch_label TEXT,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  total_rows INTEGER NOT NULL,
  missing_applicant_id INTEGER NOT NULL,
  missing_name INTEGER NOT NULL,
  missing_email INTEGER NOT NULL,
  invalid_email INTEGER NOT NULL,
  missing_program INTEGER NOT NULL,
  missing_income INTEGER NOT NULL,
  low_gpa INTEGER NOT NULL,
  invalid_gpa INTEGER NOT NULL,
  gpa_out_of_range INTEGER NOT NULL,
  first_gen INTEGER NOT NULL,
  invalid_submission_date INTEGER NOT NULL,
  future_submission_date INTEGER NOT NULL,
  duplicate_email INTEGER NOT NULL,
  duplicate_applicant_id INTEGER NOT NULL,
  flagged_applications INTEGER NOT NULL,
  flagged_rate NUMERIC(5, 2) NOT NULL,
  gpa_avg NUMERIC(4, 2),
  gpa_min NUMERIC(4, 2),
  gpa_max NUMERIC(4, 2),
  submission_start DATE,
  submission_end DATE,
  program_counts JSONB NOT NULL,
  program_gpa_avg JSONB NOT NULL,
  income_bracket_counts JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS intake_normalizer.applications (
  application_id BIGSERIAL PRIMARY KEY,
  batch_id UUID NOT NULL REFERENCES intake_normalizer.batches(batch_id) ON DELETE CASCADE,
  applicant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  program TEXT NOT NULL,
  gpa NUMERIC(4, 2),
  income_bracket TEXT,
  submission_date DATE,
  first_gen BOOLEAN NOT NULL DEFAULT FALSE,
  eligibility_notes TEXT,
  flags TEXT[] NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_intake_normalizer_program
  ON intake_normalizer.applications(program);

ALTER TABLE intake_normalizer.batches
  ADD COLUMN IF NOT EXISTS missing_program INTEGER NOT NULL DEFAULT 0;

ALTER TABLE intake_normalizer.batches
  ADD COLUMN IF NOT EXISTS gpa_out_of_range INTEGER NOT NULL DEFAULT 0;

ALTER TABLE intake_normalizer.batches
  ADD COLUMN IF NOT EXISTS missing_name INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS duplicate_applicant_id INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS flagged_applications INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS flagged_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS gpa_avg NUMERIC(4, 2),
  ADD COLUMN IF NOT EXISTS gpa_min NUMERIC(4, 2),
  ADD COLUMN IF NOT EXISTS gpa_max NUMERIC(4, 2),
  ADD COLUMN IF NOT EXISTS program_gpa_avg JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS income_bracket_counts JSONB NOT NULL DEFAULT '{}'::jsonb;
