from __future__ import annotations

import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

import psycopg
from psycopg.types.json import Json

from models import NormalizedApplication, Summary


def load_schema_sql() -> str:
    schema_path = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def resolve_db_url(cli_value: Optional[str]) -> str:
    if cli_value:
        return cli_value
    env_value = os.environ.get("GROUPSCHOLAR_INTAKE_DB_URL")
    if not env_value:
        raise ValueError("Missing database URL. Set GROUPSCHOLAR_INTAKE_DB_URL or pass --db-url.")
    return env_value


def ensure_schema(conn: psycopg.Connection) -> None:
    schema_sql = load_schema_sql()
    for statement in schema_sql.split(";"):
        statement = statement.strip()
        if not statement:
            continue
        conn.execute(statement)
    conn.commit()


def insert_batch(
    conn: psycopg.Connection,
    apps: Iterable[NormalizedApplication],
    summary: Summary,
    batch_label: Optional[str],
) -> uuid.UUID:
    batch_id = uuid.uuid4()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO intake_normalizer.batches (
                batch_id,
                batch_label,
                total_rows,
                missing_applicant_id,
                missing_name,
                missing_email,
                invalid_email,
                missing_program,
                missing_income,
                low_gpa,
                invalid_gpa,
                gpa_out_of_range,
                first_gen,
                invalid_submission_date,
                future_submission_date,
                duplicate_email,
                duplicate_applicant_id,
                flagged_applications,
                flagged_rate,
                gpa_avg,
                gpa_min,
                gpa_max,
                submission_start,
                submission_end,
                program_counts,
                program_gpa_avg,
                income_bracket_counts
            ) VALUES (
                %(batch_id)s,
                %(batch_label)s,
                %(total_rows)s,
                %(missing_applicant_id)s,
                %(missing_name)s,
                %(missing_email)s,
                %(invalid_email)s,
                %(missing_program)s,
                %(missing_income)s,
                %(low_gpa)s,
                %(invalid_gpa)s,
                %(gpa_out_of_range)s,
                %(first_gen)s,
                %(invalid_submission_date)s,
                %(future_submission_date)s,
                %(duplicate_email)s,
                %(duplicate_applicant_id)s,
                %(flagged_applications)s,
                %(flagged_rate)s,
                %(gpa_avg)s,
                %(gpa_min)s,
                %(gpa_max)s,
                %(submission_start)s,
                %(submission_end)s,
                %(program_counts)s,
                %(program_gpa_avg)s,
                %(income_bracket_counts)s
            )
            """,
            {
                "batch_id": batch_id,
                "batch_label": batch_label,
                "total_rows": summary.total_rows,
                "missing_applicant_id": summary.missing_applicant_id,
                "missing_name": summary.missing_name,
                "missing_email": summary.missing_email,
                "invalid_email": summary.invalid_email,
                "missing_program": summary.missing_program,
                "missing_income": summary.missing_income,
                "low_gpa": summary.low_gpa,
                "invalid_gpa": summary.invalid_gpa,
                "gpa_out_of_range": summary.gpa_out_of_range,
                "first_gen": summary.first_gen,
                "invalid_submission_date": summary.invalid_submission_date,
                "future_submission_date": summary.future_submission_date,
                "duplicate_email": summary.duplicate_email,
                "duplicate_applicant_id": summary.duplicate_applicant_id,
                "flagged_applications": summary.flagged_applications,
                "flagged_rate": summary.flagged_rate,
                "gpa_avg": summary.gpa_avg,
                "gpa_min": summary.gpa_min,
                "gpa_max": summary.gpa_max,
                "submission_start": summary.submission_start,
                "submission_end": summary.submission_end,
                "program_counts": Json(summary.program_counts),
                "program_gpa_avg": Json(summary.program_gpa_avg),
                "income_bracket_counts": Json(summary.income_bracket_counts),
            },
        )

        app_rows = []
        for app in apps:
            payload = asdict(app)
            app_rows.append(
                {
                    "batch_id": batch_id,
                    "applicant_id": payload["applicant_id"],
                    "name": payload["name"],
                    "email": payload["email"],
                    "program": payload["program"],
                    "gpa": payload["gpa"],
                    "income_bracket": payload["income_bracket"],
                    "submission_date": payload["submission_date"],
                    "first_gen": payload["first_gen"],
                    "eligibility_notes": payload["eligibility_notes"],
                    "flags": payload["flags"],
                }
            )

        if app_rows:
            cur.executemany(
                """
                INSERT INTO intake_normalizer.applications (
                    batch_id,
                    applicant_id,
                    name,
                    email,
                    program,
                    gpa,
                    income_bracket,
                    submission_date,
                    first_gen,
                    eligibility_notes,
                    flags
                ) VALUES (
                    %(batch_id)s,
                    %(applicant_id)s,
                    %(name)s,
                    %(email)s,
                    %(program)s,
                    %(gpa)s,
                    %(income_bracket)s,
                    %(submission_date)s,
                    %(first_gen)s,
                    %(eligibility_notes)s,
                    %(flags)s
                )
                """,
                app_rows,
            )

    conn.commit()
    return batch_id


def export_to_db(
    apps: Iterable[NormalizedApplication],
    summary: Summary,
    batch_label: Optional[str],
    db_url: Optional[str],
) -> uuid.UUID:
    resolved_url = resolve_db_url(db_url)
    with psycopg.connect(resolved_url) as conn:
        ensure_schema(conn)
        return insert_batch(conn, apps, summary, batch_label)
