#!/usr/bin/env python3
import argparse
import csv
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


@dataclass
class NormalizedApplication:
    applicant_id: str
    name: str
    email: Optional[str]
    program: str
    gpa: Optional[float]
    income_bracket: Optional[str]
    submission_date: Optional[str]
    first_gen: bool
    eligibility_notes: Optional[str]
    flags: List[str]


@dataclass
class Summary:
    total_rows: int
    missing_applicant_id: int
    missing_email: int
    invalid_email: int
    missing_income: int
    low_gpa: int
    invalid_gpa: int
    first_gen: int
    invalid_submission_date: int
    future_submission_date: int
    duplicate_email: int
    program_counts: Dict[str, int]
    submission_start: Optional[str]
    submission_end: Optional[str]


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


def read_applications(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [normalize_row_keys(row) for row in reader]


def normalize_row(row: Dict[str, str]) -> NormalizedApplication:
    email = row.get("email", "").strip() or None
    income = row.get("income_bracket", "").strip() or None
    gpa, invalid_gpa = parse_gpa(row.get("gpa", ""))
    flags = []
    if not row.get("applicant_id", "").strip():
        flags.append("missing_applicant_id")
    if not email:
        flags.append("missing_email")
    elif not is_email(email):
        flags.append("invalid_email")
    if not income:
        flags.append("missing_income")
    if gpa is not None and gpa < 2.5:
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
        program=normalize_program(row.get("program", "")),
        gpa=gpa,
        income_bracket=income,
        submission_date=submission,
        first_gen=parse_bool(row.get("first_gen", "")),
        eligibility_notes=row.get("eligibility_notes", "").strip() or None,
        flags=flags,
    )


def build_summary(apps: List[NormalizedApplication]) -> Summary:
    program_counts: Dict[str, int] = {}
    missing_applicant_id = 0
    missing_email = 0
    invalid_email = 0
    missing_income = 0
    low_gpa = 0
    invalid_gpa = 0
    first_gen = 0
    invalid_submission_date = 0
    future_submission_date = 0
    email_counts: Dict[str, int] = {}
    submission_dates: List[str] = []

    for app in apps:
        program_counts[app.program] = program_counts.get(app.program, 0) + 1
        if "missing_applicant_id" in app.flags:
            missing_applicant_id += 1
        if "missing_email" in app.flags:
            missing_email += 1
        if "invalid_email" in app.flags:
            invalid_email += 1
        if "missing_income" in app.flags:
            missing_income += 1
        if "low_gpa" in app.flags:
            low_gpa += 1
        if "invalid_gpa" in app.flags:
            invalid_gpa += 1
        if app.first_gen:
            first_gen += 1
        if "invalid_submission_date" in app.flags:
            invalid_submission_date += 1
        if "future_submission_date" in app.flags:
            future_submission_date += 1
        if app.email:
            key = app.email.strip().lower()
            email_counts[key] = email_counts.get(key, 0) + 1
        if app.submission_date:
            submission_dates.append(app.submission_date)

    duplicate_email = sum(1 for count in email_counts.values() if count > 1)
    submission_dates.sort()
    submission_start = submission_dates[0] if submission_dates else None
    submission_end = submission_dates[-1] if submission_dates else None

    return Summary(
        total_rows=len(apps),
        missing_applicant_id=missing_applicant_id,
        missing_email=missing_email,
        invalid_email=invalid_email,
        missing_income=missing_income,
        low_gpa=low_gpa,
        invalid_gpa=invalid_gpa,
        first_gen=first_gen,
        invalid_submission_date=invalid_submission_date,
        future_submission_date=future_submission_date,
        duplicate_email=duplicate_email,
        program_counts=program_counts,
        submission_start=submission_start,
        submission_end=submission_end,
    )


def write_json(apps: List[NormalizedApplication], path: Path) -> None:
    payload = [asdict(app) for app in apps]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_report(summary: Summary, path: Path) -> None:
    lines = [
        "# Intake Normalization Summary",
        "",
        f"Total applications: {summary.total_rows}",
        f"Missing applicant ID: {summary.missing_applicant_id}",
        f"Missing email: {summary.missing_email}",
        f"Invalid email: {summary.invalid_email}",
        f"Missing income: {summary.missing_income}",
        f"Low GPA (<2.5): {summary.low_gpa}",
        f"Invalid GPA: {summary.invalid_gpa}",
        f"First-gen applicants: {summary.first_gen}",
        f"Invalid submission date: {summary.invalid_submission_date}",
        f"Future submission date: {summary.future_submission_date}",
        f"Duplicate emails: {summary.duplicate_email}",
        f"Submission window: {summary.submission_start or 'n/a'} to {summary.submission_end or 'n/a'}",
        "",
        "## Applications by program",
    ]
    for program, count in sorted(summary.program_counts.items()):
        lines.append(f"- {program}: {count}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run(input_path: Path, out_path: Path, report_path: Path) -> Tuple[int, int]:
    rows = read_applications(input_path)
    apps = [normalize_row(row) for row in rows]
    summary = build_summary(apps)
    ensure_parent(out_path)
    ensure_parent(report_path)
    write_json(apps, out_path)
    write_report(summary, report_path)
    return len(apps), len(summary.program_counts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Group Scholar intake CSV data.")
    parser.add_argument("--input", required=True, help="Path to intake CSV file")
    parser.add_argument("--out", required=True, help="Path to write normalized JSON")
    parser.add_argument("--report", required=True, help="Path to write summary report")
    args = parser.parse_args()

    count, programs = run(Path(args.input), Path(args.out), Path(args.report))
    print(f"Normalized {count} applications across {programs} programs.")


if __name__ == "__main__":
    main()
