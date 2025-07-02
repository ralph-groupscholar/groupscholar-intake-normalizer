#!/usr/bin/env python3
import argparse
import csv
import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models import NormalizedApplication, Scorecard, Summary

DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"]
PROGRAM_ALIASES = {
    "stem scholars": "STEM Scholars",
    "arts catalyst": "Arts Catalyst",
    "health futures": "Health Futures",
}
HEADER_ALIASES = {
    "applicant id": "applicant_id",
    "application id": "applicant_id",
    "id": "applicant_id",
    "full name": "name",
    "applicant name": "name",
    "email address": "email",
    "program name": "program",
    "income": "income_bracket",
    "income bracket": "income_bracket",
    "submitted at": "submission_date",
    "submitted": "submission_date",
    "submission date": "submission_date",
    "first gen": "first_gen",
    "first gen status": "first_gen",
    "first-generation": "first_gen",
    "notes": "eligibility_notes",
    "eligibility note": "eligibility_notes",
}
EMAIL_AT = "@"




def parse_date(value: str) -> Optional[str]:
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_program(value: str) -> str:
    key = value.strip().lower()
    return PROGRAM_ALIASES.get(key, value.strip().title())


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"yes", "y", "true", "1"}


def parse_gpa(value: str) -> Tuple[Optional[float], bool]:
    if not value:
        return None, False
    try:
        return round(float(value), 2), False
    except ValueError:
        return None, True


def normalize_row_keys(row: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in row.items():
        raw_key = key.strip().lower()
        canonical = HEADER_ALIASES.get(raw_key, raw_key.replace(" ", "_"))
        normalized[canonical] = value
    return normalized


def is_email(value: Optional[str]) -> bool:
    if not value:
        return False
    trimmed = value.strip()
    if EMAIL_AT not in trimmed:
        return False
    local, _, domain = trimmed.partition(EMAIL_AT)
    return bool(local) and "." in domain and " " not in trimmed


def email_domain(value: str) -> Optional[str]:
    if not value:
        return None
    _, _, domain = value.strip().lower().partition(EMAIL_AT)
    return domain or None


def read_applications(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [normalize_row_keys(row) for row in reader]


def normalize_row(row: Dict[str, str]) -> NormalizedApplication:
    email = row.get("email", "").strip() or None
    income = row.get("income_bracket", "").strip() or None
    gpa, invalid_gpa = parse_gpa(row.get("gpa", ""))
    raw_program = row.get("program", "").strip()
    program = normalize_program(raw_program) if raw_program else "Unspecified"
    flags = []
    if not row.get("applicant_id", "").strip():
        flags.append("missing_applicant_id")
    if not row.get("name", "").strip():
        flags.append("missing_name")
    if not email:
        flags.append("missing_email")
    elif not is_email(email):
        flags.append("invalid_email")
    if not raw_program:
        flags.append("missing_program")
    if not income:
        flags.append("missing_income")
    if gpa is not None:
        if gpa < 0 or gpa > 4.0:
            flags.append("gpa_out_of_range")
        elif gpa < 2.5:
            flags.append("low_gpa")
    if invalid_gpa:
        flags.append("invalid_gpa")
    submission = parse_date(row.get("submission_date", ""))
    if submission is None and row.get("submission_date"):
        flags.append("invalid_submission_date")
    if submission and submission > date.today().isoformat():
        flags.append("future_submission_date")

    return NormalizedApplication(
        applicant_id=row.get("applicant_id", "").strip(),
        name=row.get("name", "").strip(),
        email=email,
        program=program,
        gpa=gpa,
        income_bracket=income,
        submission_date=submission,
        first_gen=parse_bool(row.get("first_gen", "")),
        eligibility_notes=row.get("eligibility_notes", "").strip() or None,
        flags=flags,
    )


def apply_duplicate_flags(apps: List[NormalizedApplication]) -> Tuple[int, int]:
    email_counts: Dict[str, int] = {}
    id_counts: Dict[str, int] = {}
    for app in apps:
        if app.email:
            key = app.email.strip().lower()
            email_counts[key] = email_counts.get(key, 0) + 1
        if app.applicant_id:
            key = app.applicant_id.strip().lower()
            id_counts[key] = id_counts.get(key, 0) + 1

    for app in apps:
        if app.email:
            key = app.email.strip().lower()
            if email_counts.get(key, 0) > 1 and "duplicate_email" not in app.flags:
                app.flags.append("duplicate_email")
        if app.applicant_id:
            key = app.applicant_id.strip().lower()
            if id_counts.get(key, 0) > 1 and "duplicate_applicant_id" not in app.flags:
                app.flags.append("duplicate_applicant_id")

    duplicate_email = sum(1 for count in email_counts.values() if count > 1)
    duplicate_applicant_id = sum(1 for count in id_counts.values() if count > 1)
    return duplicate_email, duplicate_applicant_id


def build_summary(
    apps: List[NormalizedApplication],
    duplicate_email: int,
    duplicate_applicant_id: int,
) -> Summary:
    program_counts: Dict[str, int] = {}
    program_gpas: Dict[str, List[float]] = {}
    missing_applicant_id = 0
    missing_name = 0
    missing_email = 0
    invalid_email = 0
    missing_program = 0
    missing_income = 0
    low_gpa = 0
    invalid_gpa = 0
    gpa_out_of_range = 0
    first_gen = 0
    invalid_submission_date = 0
    future_submission_date = 0
    submission_dates: List[str] = []
    flagged_applications = 0
    gpas: List[float] = []

    for app in apps:
        program_counts[app.program] = program_counts.get(app.program, 0) + 1
        if app.gpa is not None:
            gpas.append(app.gpa)
            program_gpas.setdefault(app.program, []).append(app.gpa)
        if "missing_applicant_id" in app.flags:
            missing_applicant_id += 1
        if "missing_name" in app.flags:
            missing_name += 1
        if "missing_email" in app.flags:
            missing_email += 1
        if "invalid_email" in app.flags:
            invalid_email += 1
        if "missing_program" in app.flags:
            missing_program += 1
        if "missing_income" in app.flags:
            missing_income += 1
        if "low_gpa" in app.flags:
            low_gpa += 1
        if "invalid_gpa" in app.flags:
            invalid_gpa += 1
        if "gpa_out_of_range" in app.flags:
            gpa_out_of_range += 1
        if app.first_gen:
            first_gen += 1
        if "invalid_submission_date" in app.flags:
            invalid_submission_date += 1
        if "future_submission_date" in app.flags:
            future_submission_date += 1
        if app.submission_date:
            submission_dates.append(app.submission_date)
        if app.flags:
            flagged_applications += 1

    submission_dates.sort()
    submission_start = submission_dates[0] if submission_dates else None
    submission_end = submission_dates[-1] if submission_dates else None
    flagged_rate = round((flagged_applications / len(apps) * 100), 1) if apps else 0.0
    gpa_avg = round(sum(gpas) / len(gpas), 2) if gpas else None
    gpa_min = min(gpas) if gpas else None
    gpa_max = max(gpas) if gpas else None
    program_gpa_avg: Dict[str, Optional[float]] = {}
    for program, values in program_gpas.items():
        program_gpa_avg[program] = round(sum(values) / len(values), 2) if values else None

    return Summary(
        total_rows=len(apps),
        missing_applicant_id=missing_applicant_id,
        missing_name=missing_name,
        missing_email=missing_email,
        invalid_email=invalid_email,
        missing_program=missing_program,
        missing_income=missing_income,
        low_gpa=low_gpa,
        invalid_gpa=invalid_gpa,
        gpa_out_of_range=gpa_out_of_range,
        first_gen=first_gen,
        invalid_submission_date=invalid_submission_date,
        future_submission_date=future_submission_date,
        duplicate_email=duplicate_email,
        duplicate_applicant_id=duplicate_applicant_id,
        flagged_applications=flagged_applications,
        flagged_rate=flagged_rate,
        gpa_avg=gpa_avg,
        gpa_min=gpa_min,
        gpa_max=gpa_max,
        program_counts=program_counts,
        program_gpa_avg=program_gpa_avg,
        submission_start=submission_start,
        submission_end=submission_end,
    )


def write_json(apps: List[NormalizedApplication], path: Path) -> None:
    payload = [asdict(app) for app in apps]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_scorecard(scorecard: Scorecard, path: Path) -> None:
    path.write_text(json.dumps(asdict(scorecard), indent=2), encoding="utf-8")


def write_report(summary: Summary, path: Path) -> None:
    lines = [
        "# Intake Normalization Summary",
        "",
        f"Total applications: {summary.total_rows}",
        f"Missing applicant ID: {summary.missing_applicant_id}",
        f"Missing applicant name: {summary.missing_name}",
        f"Missing email: {summary.missing_email}",
        f"Invalid email: {summary.invalid_email}",
        f"Missing program: {summary.missing_program}",
        f"Missing income: {summary.missing_income}",
        f"Low GPA (<2.5): {summary.low_gpa}",
        f"Invalid GPA: {summary.invalid_gpa}",
        f"GPA out of range: {summary.gpa_out_of_range}",
        f"GPA average: {summary.gpa_avg if summary.gpa_avg is not None else 'n/a'}",
        f"GPA range: {summary.gpa_min if summary.gpa_min is not None else 'n/a'} to {summary.gpa_max if summary.gpa_max is not None else 'n/a'}",
        f"First-gen applicants: {summary.first_gen}",
        f"Invalid submission date: {summary.invalid_submission_date}",
        f"Future submission date: {summary.future_submission_date}",
        f"Duplicate emails: {summary.duplicate_email}",
        f"Duplicate applicant IDs: {summary.duplicate_applicant_id}",
        f"Flagged applications: {summary.flagged_applications} ({summary.flagged_rate}%)",
        f"Submission window: {summary.submission_start or 'n/a'} to {summary.submission_end or 'n/a'}",
        "",
        "## Applications by program",
    ]
    for program, count in sorted(summary.program_counts.items()):
        lines.append(f"- {program}: {count}")
    lines.append("")
    lines.append("## GPA by program")
    for program, avg in sorted(summary.program_gpa_avg.items()):
        lines.append(f"- {program}: {avg if avg is not None else 'n/a'}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def follow_up_reason(flags: List[str]) -> str:
    labels = {
        "missing_applicant_id": "Missing applicant ID",
        "missing_name": "Missing applicant name",
        "missing_email": "Missing email",
        "invalid_email": "Invalid email",
        "missing_program": "Missing program",
        "missing_income": "Missing income bracket",
        "low_gpa": "Low GPA",
        "invalid_gpa": "Invalid GPA format",
        "gpa_out_of_range": "GPA out of range",
        "invalid_submission_date": "Invalid submission date",
        "future_submission_date": "Submission date in future",
        "duplicate_email": "Duplicate email",
        "duplicate_applicant_id": "Duplicate applicant ID",
    }
    reasons = [labels.get(flag, flag.replace("_", " ").title()) for flag in flags]
    return "; ".join(reasons)


def write_issues(apps: List[NormalizedApplication], path: Path) -> None:
    rows = []
    for app in apps:
        if not app.flags:
            continue
        rows.append(
            {
                "applicant_id": app.applicant_id,
                "name": app.name,
                "email": app.email or "",
                "program": app.program,
                "submission_date": app.submission_date or "",
                "flags": "; ".join(app.flags),
                "follow_up_reason": follow_up_reason(app.flags),
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "applicant_id",
                "name",
                "email",
                "program",
                "submission_date",
                "flags",
                "follow_up_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_scorecard(apps: List[NormalizedApplication], summary: Summary) -> Scorecard:
    flag_totals: Dict[str, int] = {}
    email_domains: Dict[str, int] = {}
    for app in apps:
        for flag in app.flags:
            flag_totals[flag] = flag_totals.get(flag, 0) + 1
        if app.email:
            domain = email_domain(app.email)
            if domain:
                email_domains[domain] = email_domains.get(domain, 0) + 1
    flag_rates = {
        flag: round(count / summary.total_rows, 4) if summary.total_rows else 0.0
        for flag, count in flag_totals.items()
    }
    return Scorecard(
        total_rows=summary.total_rows,
        flagged_applications=summary.flagged_applications,
        flagged_rate=summary.flagged_rate,
        flag_rates=flag_rates,
        program_counts=summary.program_counts,
        program_gpa_avg=summary.program_gpa_avg,
        email_domain_counts=dict(sorted(email_domains.items(), key=lambda item: item[1], reverse=True)),
        gpa_avg=summary.gpa_avg,
        gpa_min=summary.gpa_min,
        gpa_max=summary.gpa_max,
        submission_start=summary.submission_start,
        submission_end=summary.submission_end,
    )


def run(
    input_path: Path,
    out_path: Path,
    report_path: Path,
    issues_path: Optional[Path],
    scorecard_path: Optional[Path],
) -> Tuple[int, int]:
    rows = read_applications(input_path)
    apps = [normalize_row(row) for row in rows]
    duplicate_email, duplicate_applicant_id = apply_duplicate_flags(apps)
    summary = build_summary(apps, duplicate_email, duplicate_applicant_id)
    ensure_parent(out_path)
    ensure_parent(report_path)
    write_json(apps, out_path)
    write_report(summary, report_path)
    if issues_path:
        ensure_parent(issues_path)
        write_issues(apps, issues_path)
    if scorecard_path:
        ensure_parent(scorecard_path)
        scorecard = build_scorecard(apps, summary)
        write_scorecard(scorecard, scorecard_path)
    return len(apps), len(summary.program_counts)


def run_with_db(
    input_path: Path,
    out_path: Path,
    report_path: Path,
    issues_path: Optional[Path],
    scorecard_path: Optional[Path],
    db_url: Optional[str],
    batch_label: Optional[str],
) -> Tuple[int, int, str]:
    rows = read_applications(input_path)
    apps = [normalize_row(row) for row in rows]
    duplicate_email, duplicate_applicant_id = apply_duplicate_flags(apps)
    summary = build_summary(apps, duplicate_email, duplicate_applicant_id)
    ensure_parent(out_path)
    ensure_parent(report_path)
    write_json(apps, out_path)
    write_report(summary, report_path)
    if issues_path:
        ensure_parent(issues_path)
        write_issues(apps, issues_path)
    if scorecard_path:
        ensure_parent(scorecard_path)
        scorecard = build_scorecard(apps, summary)
        write_scorecard(scorecard, scorecard_path)

    from db import export_to_db

    batch_id = export_to_db(apps, summary, batch_label, db_url)
    return len(apps), len(summary.program_counts), str(batch_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Group Scholar intake CSV data.")
    parser.add_argument("--input", required=True, help="Path to intake CSV file")
    parser.add_argument("--out", required=True, help="Path to write normalized JSON")
    parser.add_argument("--report", required=True, help="Path to write summary report")
    parser.add_argument("--issues", help="Optional path to write flagged applications CSV")
    parser.add_argument("--scorecard", help="Optional path to write scorecard JSON")
    parser.add_argument("--db", action="store_true", help="Also export normalized data to Postgres")
    parser.add_argument("--db-url", help="Optional database URL override")
    parser.add_argument("--batch-label", help="Optional label for the ingestion batch")
    args = parser.parse_args()

    issues_path = Path(args.issues) if args.issues else None
    scorecard_path = Path(args.scorecard) if args.scorecard else None
    if args.db:
        count, programs, batch_id = run_with_db(
            Path(args.input),
            Path(args.out),
            Path(args.report),
            issues_path,
            scorecard_path,
            args.db_url,
            args.batch_label,
        )
        print(f"Normalized {count} applications across {programs} programs.")
        print(f"Exported batch {batch_id} to Postgres.")
    else:
        count, programs = run(
            Path(args.input),
            Path(args.out),
            Path(args.report),
            issues_path,
            scorecard_path,
        )
        print(f"Normalized {count} applications across {programs} programs.")


if __name__ == "__main__":
    main()
