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
                missing_phone,
                invalid_phone,
                missing_program,
                missing_school_type,
                missing_referral_source,
                missing_income,
                missing_citizenship_status,
                unrecognized_citizenship_status,
                low_gpa,
                invalid_gpa,
                gpa_out_of_range,
                first_gen,
                first_gen_rate,
                invalid_submission_date,
                future_submission_date,
                missing_submission_date,
                stale_submission,
                missing_graduation_year,
                invalid_graduation_year,
                graduation_year_out_of_range,
                duplicate_email,
                duplicate_applicant_id,
                duplicate_phone,
                flagged_applications,
                flagged_rate,
                gpa_avg,
                gpa_min,
                gpa_max,
                submission_start,
                submission_end,
                program_counts,
                program_gpa_avg,
                first_gen_program_counts,
                first_gen_program_rates,
                school_type_counts,
                referral_source_counts,
                income_bracket_counts,
                citizenship_status_counts,
                note_tag_counts,
                email_domain_counts,
                email_domain_category_counts,
                phone_country_counts,
                contact_channel_counts,
                submission_weekday_counts,
                review_status_counts,
                review_priority_counts,
                flag_severity_counts,
                data_quality_avg,
                data_quality_min,
                data_quality_max,
                quality_tier_counts,
                readiness_avg,
                readiness_min,
                readiness_max,
                readiness_bucket_counts,
                submission_age_avg,
                submission_age_min,
                submission_age_max,
                submission_age_bucket_counts,
                submission_recency_counts,
                graduation_year_counts,
                graduation_year_bucket_counts
            ) VALUES (
                %(batch_id)s,
                %(batch_label)s,
                %(total_rows)s,
                %(missing_applicant_id)s,
                %(missing_name)s,
                %(missing_email)s,
                %(invalid_email)s,
                %(missing_phone)s,
                %(invalid_phone)s,
                %(missing_program)s,
                %(missing_school_type)s,
                %(missing_referral_source)s,
                %(missing_income)s,
                %(missing_citizenship_status)s,
                %(unrecognized_citizenship_status)s,
                %(low_gpa)s,
                %(invalid_gpa)s,
                %(gpa_out_of_range)s,
                %(first_gen)s,
                %(first_gen_rate)s,
                %(invalid_submission_date)s,
                %(future_submission_date)s,
                %(missing_submission_date)s,
                %(stale_submission)s,
                %(missing_graduation_year)s,
                %(invalid_graduation_year)s,
                %(graduation_year_out_of_range)s,
                %(duplicate_email)s,
                %(duplicate_applicant_id)s,
                %(duplicate_phone)s,
                %(flagged_applications)s,
                %(flagged_rate)s,
                %(gpa_avg)s,
                %(gpa_min)s,
                %(gpa_max)s,
                %(submission_start)s,
                %(submission_end)s,
                %(program_counts)s,
                %(program_gpa_avg)s,
                %(first_gen_program_counts)s,
                %(first_gen_program_rates)s,
                %(school_type_counts)s,
                %(referral_source_counts)s,
                %(income_bracket_counts)s,
                %(citizenship_status_counts)s,
                %(note_tag_counts)s,
                %(email_domain_counts)s,
                %(email_domain_category_counts)s,
                %(phone_country_counts)s,
                %(contact_channel_counts)s,
                %(submission_weekday_counts)s,
                %(review_status_counts)s,
                %(review_priority_counts)s,
                %(flag_severity_counts)s,
                %(data_quality_avg)s,
                %(data_quality_min)s,
                %(data_quality_max)s,
                %(quality_tier_counts)s,
                %(readiness_avg)s,
                %(readiness_min)s,
                %(readiness_max)s,
                %(readiness_bucket_counts)s,
                %(submission_age_avg)s,
                %(submission_age_min)s,
                %(submission_age_max)s,
                %(submission_age_bucket_counts)s,
                %(submission_recency_counts)s,
                %(graduation_year_counts)s,
                %(graduation_year_bucket_counts)s
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
                "missing_phone": summary.missing_phone,
                "invalid_phone": summary.invalid_phone,
                "missing_program": summary.missing_program,
                "missing_school_type": summary.missing_school_type,
                "missing_referral_source": summary.missing_referral_source,
                "missing_income": summary.missing_income,
                "missing_citizenship_status": summary.missing_citizenship_status,
                "unrecognized_citizenship_status": summary.unrecognized_citizenship_status,
                "low_gpa": summary.low_gpa,
                "invalid_gpa": summary.invalid_gpa,
                "gpa_out_of_range": summary.gpa_out_of_range,
                "first_gen": summary.first_gen,
                "first_gen_rate": summary.first_gen_rate,
                "invalid_submission_date": summary.invalid_submission_date,
                "future_submission_date": summary.future_submission_date,
                "missing_submission_date": summary.missing_submission_date,
                "stale_submission": summary.stale_submission,
                "missing_graduation_year": summary.missing_graduation_year,
                "invalid_graduation_year": summary.invalid_graduation_year,
                "graduation_year_out_of_range": summary.graduation_year_out_of_range,
                "duplicate_email": summary.duplicate_email,
                "duplicate_applicant_id": summary.duplicate_applicant_id,
                "duplicate_phone": summary.duplicate_phone,
                "flagged_applications": summary.flagged_applications,
                "flagged_rate": summary.flagged_rate,
                "gpa_avg": summary.gpa_avg,
                "gpa_min": summary.gpa_min,
                "gpa_max": summary.gpa_max,
                "submission_start": summary.submission_start,
                "submission_end": summary.submission_end,
                "program_counts": Json(summary.program_counts),
                "program_gpa_avg": Json(summary.program_gpa_avg),
                "first_gen_program_counts": Json(summary.first_gen_program_counts),
                "first_gen_program_rates": Json(summary.first_gen_program_rates),
                "school_type_counts": Json(summary.school_type_counts),
                "referral_source_counts": Json(summary.referral_source_counts),
                "income_bracket_counts": Json(summary.income_bracket_counts),
                "citizenship_status_counts": Json(summary.citizenship_status_counts),
                "note_tag_counts": Json(summary.note_tag_counts),
                "email_domain_counts": Json(summary.email_domain_counts),
                "email_domain_category_counts": Json(summary.email_domain_category_counts),
                "phone_country_counts": Json(summary.phone_country_counts),
                "contact_channel_counts": Json(summary.contact_channel_counts),
                "submission_weekday_counts": Json(summary.submission_weekday_counts),
                "review_status_counts": Json(summary.review_status_counts),
                "review_priority_counts": Json(summary.review_priority_counts),
                "flag_severity_counts": Json(summary.flag_severity_counts),
                "data_quality_avg": summary.data_quality_avg,
                "data_quality_min": summary.data_quality_min,
                "data_quality_max": summary.data_quality_max,
                "quality_tier_counts": Json(summary.quality_tier_counts),
                "readiness_avg": summary.readiness_avg,
                "readiness_min": summary.readiness_min,
                "readiness_max": summary.readiness_max,
                "readiness_bucket_counts": Json(summary.readiness_bucket_counts),
                "submission_age_avg": summary.submission_age_avg,
                "submission_age_min": summary.submission_age_min,
                "submission_age_max": summary.submission_age_max,
                "submission_age_bucket_counts": Json(summary.submission_age_bucket_counts),
                "submission_recency_counts": Json(summary.submission_recency_counts),
                "graduation_year_counts": Json(summary.graduation_year_counts),
                "graduation_year_bucket_counts": Json(summary.graduation_year_bucket_counts),
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
                    "phone": payload["phone"],
                    "phone_normalized": payload["phone_normalized"],
                    "phone_country": payload["phone_country"],
                    "contact_channel": payload["contact_channel"],
                    "email_domain_category": payload["email_domain_category"],
                    "program": payload["program"],
                    "school_type": payload["school_type"],
                    "referral_source": payload["referral_source"],
                    "gpa": payload["gpa"],
                    "income_bracket": payload["income_bracket"],
                    "citizenship_status": payload["citizenship_status"],
                    "submission_date": payload["submission_date"],
                    "submission_age_days": payload["submission_age_days"],
                    "submission_age_bucket": payload["submission_age_bucket"],
                    "submission_recency": payload["submission_recency"],
                    "graduation_year": payload["graduation_year"],
                    "graduation_year_bucket": payload["graduation_year_bucket"],
                    "first_gen": payload["first_gen"],
                    "eligibility_notes": payload["eligibility_notes"],
                    "note_tags": payload["note_tags"],
                    "flags": payload["flags"],
                    "flag_severity": payload["flag_severity"],
                    "review_status": payload["review_status"],
                    "review_priority": payload["review_priority"],
                    "data_quality_score": payload["data_quality_score"],
                    "readiness_score": payload["readiness_score"],
                    "readiness_bucket": payload["readiness_bucket"],
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
                    phone,
                    phone_normalized,
                    phone_country,
                    contact_channel,
                    email_domain_category,
                    program,
                    school_type,
                    referral_source,
                    gpa,
                    income_bracket,
                    citizenship_status,
                    submission_date,
                    submission_age_days,
                    submission_age_bucket,
                    submission_recency,
                    graduation_year,
                    graduation_year_bucket,
                    first_gen,
                    eligibility_notes,
                    note_tags,
                    flags,
                    flag_severity,
                    review_status,
                    review_priority,
                    data_quality_score,
                    readiness_score,
                    readiness_bucket
                ) VALUES (
                    %(batch_id)s,
                    %(applicant_id)s,
                    %(name)s,
                    %(email)s,
                    %(phone)s,
                    %(phone_normalized)s,
                    %(phone_country)s,
                    %(contact_channel)s,
                    %(email_domain_category)s,
                    %(program)s,
                    %(school_type)s,
                    %(referral_source)s,
                    %(gpa)s,
                    %(income_bracket)s,
                    %(citizenship_status)s,
                    %(submission_date)s,
                    %(submission_age_days)s,
                    %(submission_age_bucket)s,
                    %(submission_recency)s,
                    %(graduation_year)s,
                    %(graduation_year_bucket)s,
                    %(first_gen)s,
                    %(eligibility_notes)s,
                    %(note_tags)s,
                    %(flags)s,
                    %(flag_severity)s,
                    %(review_status)s,
                    %(review_priority)s,
                    %(data_quality_score)s,
                    %(readiness_score)s,
                    %(readiness_bucket)s
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
