#!/usr/bin/env python3
import argparse
import csv
import json
import re
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models import NormalizedApplication, Scorecard, Summary

DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"]
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%m/%d/%Y %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
]
PROGRAM_ALIASES = {
    "stem scholars": "STEM Scholars",
    "arts catalyst": "Arts Catalyst",
    "health futures": "Health Futures",
}
REFERRAL_SOURCE_ALIASES = {
    "school counselor": "School Counselor",
    "counselor": "School Counselor",
    "guidance counselor": "School Counselor",
    "teacher": "Teacher",
    "alumni": "Alumni",
    "alum": "Alumni",
    "peer": "Peer Referral",
    "friend": "Peer Referral",
    "peer referral": "Peer Referral",
    "parent": "Parent/Guardian",
    "guardian": "Parent/Guardian",
    "parent/guardian": "Parent/Guardian",
    "website": "Website",
    "web": "Website",
    "search": "Web Search",
    "web search": "Web Search",
    "instagram": "Social Media",
    "tiktok": "Social Media",
    "linkedin": "Social Media",
    "social": "Social Media",
    "social media": "Social Media",
    "email": "Email Campaign",
    "email campaign": "Email Campaign",
    "newsletter": "Email Campaign",
    "partner org": "Partner Organization",
    "partner organization": "Partner Organization",
    "community org": "Partner Organization",
    "community organization": "Partner Organization",
    "event": "Event",
    "info session": "Event",
}
INCOME_ALIASES = {
    "<=40k": "<=40k",
    "<40k": "<=40k",
    "under40k": "<=40k",
    "0-40k": "<=40k",
    "40k-70k": "40k-70k",
    "40kto70k": "40k-70k",
    "40k–70k": "40k-70k",
    "70k-100k": "70k-100k",
    "70kto100k": "70k-100k",
    "70k–100k": "70k-100k",
    "100k+": "100k+",
    "100kplus": "100k+",
    ">=100k": "100k+",
    ">100k": "100k+",
}
NOTE_TAG_RULES = {
    "missing_essay": ["missing essay", "essay draft", "essay missing"],
    "missing_recommendation": ["missing recommendation", "needs recommendation", "recommendation letter"],
    "income_verification_pending": ["income verification pending", "income verification"],
    "documents_complete": ["all docs complete", "docs complete", "documents complete"],
    "gpa_review": ["gpa needs review", "gpa review"],
}
REVIEW_STATUS_ORDER = ["incomplete", "needs_review", "needs_follow_up", "ready"]
REVIEW_PRIORITY_ORDER = ["high", "medium", "low", "ready"]
FLAG_SEVERITY_ORDER = ["critical", "high", "medium", "clean"]
QUALITY_TIERS = [
    ("excellent", 90),
    ("good", 75),
    ("needs_attention", 50),
    ("critical", 0),
]
WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SUBMISSION_TIME_BUCKET_ORDER = [
    "early_morning",
    "morning",
    "afternoon",
    "evening",
    "late_night",
    "unknown",
]
READINESS_BUCKETS = [
    ("ready", 85),
    ("needs_follow_up", 65),
    ("needs_review", 45),
    ("incomplete", 0),
]
SUBMISSION_AGE_BUCKETS = [
    ("0-7 days", 7),
    ("8-14 days", 14),
    ("15-30 days", 30),
    ("31-60 days", 60),
    ("61-90 days", 90),
    ("90+ days", 10_000),
]
SUBMISSION_RECENCY_BUCKETS = [
    ("fresh", 7),
    ("active", 30),
    ("stale", 60),
    ("backlog", 90),
    ("archive", 10_000),
]
GRADUATION_YEAR_BUCKETS = ["overdue", "current", "next_year", "future", "unknown"]
GRAD_YEAR_MIN_OFFSET = -1
GRAD_YEAR_MAX_OFFSET = 6
STALE_SUBMISSION_DAYS = 30
CRITICAL_FLAGS = {
    "missing_applicant_id",
    "missing_name",
    "missing_email",
    "invalid_email",
    "missing_program",
    "invalid_submission_date",
}
HIGH_FLAGS = {
    "gpa_out_of_range",
    "invalid_gpa",
    "future_submission_date",
    "missing_submission_date",
    "graduation_year_out_of_range",
    "invalid_graduation_year",
    "missing_citizenship_status",
    "unrecognized_citizenship_status",
}
HEADER_ALIASES = {
    "applicant id": "applicant_id",
    "application id": "applicant_id",
    "id": "applicant_id",
    "full name": "name",
    "applicant name": "name",
    "email address": "email",
    "phone": "phone",
    "phone number": "phone",
    "phone_number": "phone",
    "mobile": "phone",
    "mobile phone": "phone",
    "cell": "phone",
    "cell phone": "phone",
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
    "referral source": "referral_source",
    "source": "referral_source",
    "channel": "referral_source",
    "referred by": "referral_source",
    "citizenship status": "citizenship_status",
    "citizenship": "citizenship_status",
    "citizenship_status": "citizenship_status",
    "graduation year": "graduation_year",
    "grad year": "graduation_year",
    "grad_year": "graduation_year",
    "expected graduation year": "graduation_year",
    "school type": "school_type",
    "school_type": "school_type",
    "school category": "school_type",
    "school sector": "school_type",
    "school": "school_type",
    "citizenship status": "citizenship_status",
    "citizenship": "citizenship_status",
    "citizenship_status": "citizenship_status",
}
EMAIL_AT = "@"
PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "live.com",
}
EMAIL_DOMAIN_CATEGORY_ORDER = [
    "education",
    "nonprofit",
    "government",
    "network",
    "personal",
    "commercial",
    "other",
    "invalid",
    "missing",
]
CONTACT_CHANNEL_ORDER = ["email_and_phone", "email_only", "phone_only", "missing"]
SCHOOL_TYPE_ALIASES = {
    "public": "Public",
    "public school": "Public",
    "private": "Private",
    "private school": "Private",
    "charter": "Charter",
    "charter school": "Charter",
    "homeschool": "Homeschool",
    "home school": "Homeschool",
    "homeschooled": "Homeschool",
    "international": "International",
    "international school": "International",
    "community college": "Community College",
    "two year college": "Community College",
    "two-year college": "Community College",
    "college": "College",
    "university": "University",
    "trade school": "Trade School",
    "vocational": "Trade School",
    "vocational school": "Trade School",
}
SCHOOL_TYPE_ORDER = [
    "Public",
    "Charter",
    "Private",
    "Homeschool",
    "Community College",
    "College",
    "University",
    "Trade School",
    "International",
    "Other",
    "Missing",
]
CITIZENSHIP_STATUS_ALIASES = {
    "us citizen": "US Citizen",
    "u.s. citizen": "US Citizen",
    "usa citizen": "US Citizen",
    "citizen": "US Citizen",
    "permanent resident": "Permanent Resident",
    "green card": "Permanent Resident",
    "resident": "Permanent Resident",
    "daca": "DACA",
    "dreamer": "DACA",
    "international": "International",
    "international student": "International",
    "undocumented": "Undocumented",
    "non citizen": "Undocumented",
    "other": "Other",
    "prefer not to say": "Other",
}
CITIZENSHIP_STATUS_ORDER = [
    "US Citizen",
    "Permanent Resident",
    "DACA",
    "Undocumented",
    "International",
    "Other",
    "Missing",
]
CITIZENSHIP_ALIASES = {
    "us citizen": "US Citizen",
    "u.s. citizen": "US Citizen",
    "citizen": "US Citizen",
    "us": "US Citizen",
    "usa": "US Citizen",
    "american": "US Citizen",
    "permanent resident": "Permanent Resident",
    "green card": "Permanent Resident",
    "daca": "DACA",
    "dreamer": "DACA",
    "international": "International",
    "intl": "International",
    "f-1": "International",
    "undocumented": "Undocumented",
    "no status": "Undocumented",
    "other": "Other",
}
CITIZENSHIP_STATUS_ORDER = [
    "US Citizen",
    "Permanent Resident",
    "DACA",
    "International",
    "Undocumented",
    "Other",
    "Missing",
]
PHONE_COUNTRY_PREFIXES = [
    ("1", "US/Canada"),
    ("44", "United Kingdom"),
    ("91", "India"),
    ("61", "Australia"),
    ("81", "Japan"),
    ("49", "Germany"),
    ("33", "France"),
    ("34", "Spain"),
    ("39", "Italy"),
    ("52", "Mexico"),
    ("55", "Brazil"),
    ("234", "Nigeria"),
    ("27", "South Africa"),
]
PHONE_COUNTRY_PREFIX_ORDER = sorted(PHONE_COUNTRY_PREFIXES, key=lambda item: len(item[0]), reverse=True)
PHONE_COUNTRY_ORDER = [
    "US/Canada",
    "United Kingdom",
    "India",
    "Australia",
    "Japan",
    "Germany",
    "France",
    "Spain",
    "Italy",
    "Mexico",
    "Brazil",
    "Nigeria",
    "South Africa",
    "International",
    "invalid",
    "missing",
]




def parse_submission_datetime(value: str) -> Tuple[Optional[str], Optional[int]]:
    if not value:
        return None, None
    raw = value.strip()
    if not raw:
        return None, None
    for fmt in DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.date().isoformat(), parsed.hour
        except ValueError:
            continue
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.date().isoformat(), None
        except ValueError:
            continue
    return None, None


def parse_date(value: str) -> Optional[str]:
    parsed_date, _ = parse_submission_datetime(value)
    return parsed_date


def normalize_program(value: str) -> str:
    key = value.strip().lower()
    return PROGRAM_ALIASES.get(key, value.strip().title())


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"yes", "y", "true", "1"}


def normalize_referral_source(value: str) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    key = raw.lower().replace("-", " ").replace("/", " ").strip()
    key = " ".join(key.split())
    return REFERRAL_SOURCE_ALIASES.get(key, raw.title())


def normalize_income_bracket(value: str) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    key = raw.lower().replace(" ", "").replace("$", "").replace(",", "")
    alias = INCOME_ALIASES.get(key)
    if alias:
        return alias

    range_match = re.match(r"^(\d+)(k)?-(\d+)(k)?$", key)
    if range_match:
        low = int(range_match.group(1)) * (1000 if range_match.group(2) else 1)
        high = int(range_match.group(3)) * (1000 if range_match.group(4) else 1)
        if high <= 40000:
            return "<=40k"
        if high <= 70000:
            return "40k-70k"
        if high <= 100000:
            return "70k-100k"
        return "100k+"

    bound_match = re.match(r"^(<=|>=|<|>)(\d+)(k)?$", key)
    if bound_match:
        amount = int(bound_match.group(2)) * (1000 if bound_match.group(3) else 1)
        if amount <= 40000:
            return "<=40k"
        if amount <= 70000:
            return "40k-70k"
        if amount <= 100000:
            return "70k-100k"
        return "100k+"

    return raw


def normalize_school_type(value: str) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    key = raw.lower().replace("-", " ").replace("/", " ").strip()
    key = " ".join(key.split())
    return SCHOOL_TYPE_ALIASES.get(key, raw.title())


def normalize_citizenship_status(value: str) -> Tuple[Optional[str], bool]:
    if not value:
        return None, False
    raw = value.strip()
    if not raw:
        return None, False
    key = raw.lower().replace("-", " ").replace("/", " ").strip()
    key = " ".join(key.split())
    normalized = CITIZENSHIP_STATUS_ALIASES.get(key)
    if normalized:
        return normalized, False
    return "Other", True


def normalize_citizenship_status(value: str) -> Tuple[Optional[str], bool]:
    if not value:
        return None, False
    raw = value.strip()
    if not raw:
        return None, False
    key = raw.lower().replace("-", " ").replace("/", " ").strip()
    key = " ".join(key.split())
    if key in CITIZENSHIP_ALIASES:
        return CITIZENSHIP_ALIASES[key], False
    return "Other", True


def parse_gpa(value: str) -> Tuple[Optional[float], bool]:
    if not value:
        return None, False
    try:
        return round(float(value), 2), False
    except ValueError:
        return None, True


def parse_graduation_year(value: str) -> Tuple[Optional[int], bool]:
    if not value:
        return None, False
    raw = value.strip()
    if not raw:
        return None, False
    if not raw.isdigit():
        return None, True
    return int(raw), False


def graduation_year_bucket(year: Optional[int]) -> str:
    if year is None:
        return "unknown"
    current_year = date.today().year
    if year < current_year:
        return "overdue"
    if year == current_year:
        return "current"
    if year == current_year + 1:
        return "next_year"
    return "future"


def extract_note_tags(value: Optional[str]) -> List[str]:
    if not value:
        return []
    text = value.strip().lower()
    if not text:
        return []
    tags: List[str] = []
    for tag, phrases in NOTE_TAG_RULES.items():
        if any(phrase in text for phrase in phrases):
            tags.append(tag)
    return tags


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


def email_domain_category(value: Optional[str]) -> str:
    if not value:
        return "missing"
    if not is_email(value):
        return "invalid"
    domain = email_domain(value)
    if not domain:
        return "invalid"
    if domain.endswith(".edu"):
        return "education"
    if domain.endswith(".org"):
        return "nonprofit"
    if domain.endswith(".gov"):
        return "government"
    if domain.endswith(".net"):
        return "network"
    if domain in PERSONAL_EMAIL_DOMAINS:
        return "personal"
    if domain.endswith(".com"):
        return "commercial"
    return "other"


def contact_channel(email: Optional[str], phone_normalized: Optional[str]) -> str:
    has_email = is_email(email)
    has_phone = bool(phone_normalized)
    if has_email and has_phone:
        return "email_and_phone"
    if has_email:
        return "email_only"
    if has_phone:
        return "phone_only"
    return "missing"


def normalize_phone(value: str) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    raw = value.strip() if value else ""
    if not raw:
        return None, None, None, False
    cleaned = re.sub(r"(ext\.?|x|#)\s*\d+$", "", raw, flags=re.IGNORECASE).strip()
    if re.search(r"[A-Za-z]", cleaned):
        return raw, None, None, True
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return raw, None, None, True
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 10:
        return raw, f"+1{digits}", "US/Canada", False
    if len(digits) == 11 and digits.startswith("1"):
        return raw, f"+{digits}", "US/Canada", False
    if 11 <= len(digits) <= 15:
        country = "International"
        for prefix, label in PHONE_COUNTRY_PREFIX_ORDER:
            if digits.startswith(prefix):
                country = label
                break
        return raw, f"+{digits}", country, False
    return raw, None, None, True


def read_applications(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [normalize_row_keys(row) for row in reader]


def normalize_row(row: Dict[str, str]) -> NormalizedApplication:
    email = row.get("email", "").strip() or None
    email_category = email_domain_category(email)
    has_phone_field = "phone" in row
    phone_value = row.get("phone", "").strip() if has_phone_field else ""
    phone_raw, phone_normalized, phone_country, invalid_phone = normalize_phone(phone_value)
    contact_channel_value = contact_channel(email, phone_normalized)
    income = normalize_income_bracket(row.get("income_bracket", ""))
    gpa, invalid_gpa = parse_gpa(row.get("gpa", ""))
    graduation_year, invalid_graduation_year = parse_graduation_year(
        row.get("graduation_year", "")
    )
    raw_program = row.get("program", "").strip()
    program = normalize_program(raw_program) if raw_program else "Unspecified"
    school_type = normalize_school_type(row.get("school_type", ""))
    citizenship_status, citizenship_unrecognized = normalize_citizenship_status(
        row.get("citizenship_status", "")
    )
    referral_source = normalize_referral_source(row.get("referral_source", ""))
    eligibility_notes = row.get("eligibility_notes", "").strip() or None
    note_tags = extract_note_tags(eligibility_notes)
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
    if not school_type:
        flags.append("missing_school_type")
    if not citizenship_status:
        flags.append("missing_citizenship_status")
    if citizenship_unrecognized:
        flags.append("unrecognized_citizenship_status")
    if has_phone_field and not phone_raw:
        flags.append("missing_phone")
    elif phone_raw and invalid_phone:
        flags.append("invalid_phone")
    if not referral_source:
        flags.append("missing_referral_source")
    if not income:
        flags.append("missing_income")
    if gpa is not None:
        if gpa < 0 or gpa > 4.0:
            flags.append("gpa_out_of_range")
        elif gpa < 2.5:
            flags.append("low_gpa")
    if invalid_gpa:
        flags.append("invalid_gpa")
    if not row.get("graduation_year", "").strip():
        flags.append("missing_graduation_year")
    if invalid_graduation_year:
        flags.append("invalid_graduation_year")
    if graduation_year is not None:
        current_year = date.today().year
        if (
            graduation_year < current_year + GRAD_YEAR_MIN_OFFSET
            or graduation_year > current_year + GRAD_YEAR_MAX_OFFSET
        ):
            flags.append("graduation_year_out_of_range")
    submission_value = row.get("submission_date", "")
    submission, submission_hour = parse_submission_datetime(submission_value)
    submission_time_bucket_value = submission_time_bucket(submission_hour)
    if submission is None and submission_value:
        flags.append("invalid_submission_date")
    if not submission_value.strip():
        flags.append("missing_submission_date")
    if submission and submission > date.today().isoformat():
        flags.append("future_submission_date")

    submission_age_days = None
    submission_age_bucket_value = None
    if submission:
        days_delta = (date.today() - date.fromisoformat(submission)).days
        if days_delta >= 0:
            submission_age_days = days_delta
            submission_age_bucket_value = submission_age_bucket(days_delta)
        else:
            submission_age_bucket_value = "future"
    if submission_age_days is not None and submission_age_days >= STALE_SUBMISSION_DAYS:
        flags.append("stale_submission")
    submission_recency_value = submission_recency(submission_age_days)

    review_status, review_priority = derive_review_status(flags)
    data_quality_score = compute_quality_score(flags)
    readiness_score = compute_readiness_score(flags)
    readiness_bucket_value = readiness_bucket(readiness_score)
    flag_severity_value = flag_severity(flags)
    graduation_year_bucket_value = graduation_year_bucket(graduation_year)
    return NormalizedApplication(
        applicant_id=row.get("applicant_id", "").strip(),
        name=row.get("name", "").strip(),
        email=email,
        phone=phone_raw,
        phone_normalized=phone_normalized,
        phone_country=phone_country,
        contact_channel=contact_channel_value,
        email_domain_category=email_category,
        program=program,
        school_type=school_type,
        referral_source=referral_source,
        gpa=gpa,
        income_bracket=income,
        citizenship_status=citizenship_status,
        submission_date=submission,
        submission_hour=submission_hour,
        submission_time_bucket=submission_time_bucket_value,
        submission_age_days=submission_age_days,
        submission_age_bucket=submission_age_bucket_value,
        submission_recency=submission_recency_value,
        first_gen=parse_bool(row.get("first_gen", "")),
        eligibility_notes=eligibility_notes,
        note_tags=note_tags,
        flags=flags,
        flag_severity=flag_severity_value,
        review_status=review_status,
        review_priority=review_priority,
        data_quality_score=data_quality_score,
        readiness_score=readiness_score,
        readiness_bucket=readiness_bucket_value,
        graduation_year=graduation_year,
        graduation_year_bucket=graduation_year_bucket_value,
    )


def apply_duplicate_flags(apps: List[NormalizedApplication]) -> Tuple[int, int, int]:
    email_counts: Dict[str, int] = {}
    id_counts: Dict[str, int] = {}
    phone_counts: Dict[str, int] = {}
    for app in apps:
        if app.email:
            key = app.email.strip().lower()
            email_counts[key] = email_counts.get(key, 0) + 1
        if app.applicant_id:
            key = app.applicant_id.strip().lower()
            id_counts[key] = id_counts.get(key, 0) + 1
        if app.phone_normalized:
            key = app.phone_normalized.strip()
            phone_counts[key] = phone_counts.get(key, 0) + 1

    for app in apps:
        if app.email:
            key = app.email.strip().lower()
            if email_counts.get(key, 0) > 1 and "duplicate_email" not in app.flags:
                app.flags.append("duplicate_email")
        if app.applicant_id:
            key = app.applicant_id.strip().lower()
            if id_counts.get(key, 0) > 1 and "duplicate_applicant_id" not in app.flags:
                app.flags.append("duplicate_applicant_id")
        if app.phone_normalized:
            key = app.phone_normalized.strip()
            if phone_counts.get(key, 0) > 1 and "duplicate_phone" not in app.flags:
                app.flags.append("duplicate_phone")

    duplicate_email = sum(1 for count in email_counts.values() if count > 1)
    duplicate_applicant_id = sum(1 for count in id_counts.values() if count > 1)
    duplicate_phone = sum(1 for count in phone_counts.values() if count > 1)
    return duplicate_email, duplicate_applicant_id, duplicate_phone


def derive_review_status(flags: List[str]) -> Tuple[str, str]:
    if any(flag in CRITICAL_FLAGS for flag in flags):
        return "incomplete", "high"
    if any(flag in HIGH_FLAGS for flag in flags):
        return "needs_review", "medium"
    if flags:
        return "needs_follow_up", "low"
    return "ready", "ready"


def flag_severity(flags: List[str]) -> str:
    if any(flag in CRITICAL_FLAGS for flag in flags):
        return "critical"
    if any(flag in HIGH_FLAGS for flag in flags):
        return "high"
    if flags:
        return "medium"
    return "clean"


def compute_quality_score(flags: List[str]) -> int:
    score = 100
    for flag in flags:
        if flag in CRITICAL_FLAGS:
            score -= 25
        elif flag in HIGH_FLAGS:
            score -= 10
        else:
            score -= 5
    return max(0, score)


def compute_readiness_score(flags: List[str]) -> int:
    score = 100
    for flag in flags:
        if flag in CRITICAL_FLAGS:
            score -= 30
        elif flag in HIGH_FLAGS:
            score -= 15
        else:
            score -= 8
    return max(0, score)


def quality_tier(score: int) -> str:
    for tier, cutoff in QUALITY_TIERS:
        if score >= cutoff:
            return tier
    return "critical"


def readiness_bucket(score: int) -> str:
    for bucket, cutoff in READINESS_BUCKETS:
        if score >= cutoff:
            return bucket
    return "incomplete"


def submission_age_bucket(age_days: int) -> str:
    for bucket, cutoff in SUBMISSION_AGE_BUCKETS:
        if age_days <= cutoff:
            return bucket
    return "90+ days"


def submission_recency(age_days: Optional[int]) -> str:
    if age_days is None:
        return "missing"
    if age_days < 0:
        return "future"
    for bucket, cutoff in SUBMISSION_RECENCY_BUCKETS:
        if age_days <= cutoff:
            return bucket
    return "archive"


def submission_time_bucket(hour: Optional[int]) -> str:
    if hour is None:
        return "unknown"
    if 5 <= hour <= 8:
        return "early_morning"
    if 9 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 16:
        return "afternoon"
    if 17 <= hour <= 20:
        return "evening"
    return "late_night"


def update_review_status(apps: List[NormalizedApplication]) -> None:
    for app in apps:
        app.review_status, app.review_priority = derive_review_status(app.flags)
        app.data_quality_score = compute_quality_score(app.flags)
        app.readiness_score = compute_readiness_score(app.flags)
        app.readiness_bucket = readiness_bucket(app.readiness_score)
        app.flag_severity = flag_severity(app.flags)
        if app.submission_date:
            days_delta = (date.today() - date.fromisoformat(app.submission_date)).days
            if days_delta >= 0:
                app.submission_age_days = days_delta
                app.submission_age_bucket = submission_age_bucket(days_delta)
            else:
                app.submission_age_days = None
                app.submission_age_bucket = "future"
        app.submission_recency = submission_recency(app.submission_age_days)
        if app.submission_age_days is not None and app.submission_age_days >= STALE_SUBMISSION_DAYS:
            if "stale_submission" not in app.flags:
                app.flags.append("stale_submission")
        else:
            if "stale_submission" in app.flags:
                app.flags.remove("stale_submission")
        app.graduation_year_bucket = graduation_year_bucket(app.graduation_year)


def build_summary(
    apps: List[NormalizedApplication],
    duplicate_email: int,
    duplicate_applicant_id: int,
    duplicate_phone: int,
) -> Summary:
    program_counts: Dict[str, int] = {}
    program_gpas: Dict[str, List[float]] = {}
    first_gen_program_counts: Dict[str, int] = {}
    referral_source_counts: Dict[str, int] = {}
    income_bracket_counts: Dict[str, int] = {}
    citizenship_status_counts: Dict[str, int] = {}
    note_tag_counts: Dict[str, int] = {}
    email_domain_counts: Dict[str, int] = {}
    email_domain_category_counts: Dict[str, int] = {}
    phone_country_counts: Dict[str, int] = {}
    contact_channel_counts: Dict[str, int] = {}
    school_type_counts: Dict[str, int] = {}
    submission_weekday_counts: Dict[str, int] = {}
    submission_time_bucket_counts: Dict[str, int] = {}
    review_status_counts: Dict[str, int] = {}
    review_priority_counts: Dict[str, int] = {}
    flag_severity_counts: Dict[str, int] = {}
    missing_applicant_id = 0
    missing_name = 0
    missing_email = 0
    invalid_email = 0
    missing_phone = 0
    invalid_phone = 0
    missing_program = 0
    missing_school_type = 0
    missing_referral_source = 0
    missing_income = 0
    missing_citizenship_status = 0
    unrecognized_citizenship_status = 0
    low_gpa = 0
    invalid_gpa = 0
    gpa_out_of_range = 0
    missing_graduation_year = 0
    invalid_graduation_year = 0
    graduation_year_out_of_range = 0
    first_gen = 0
    invalid_submission_date = 0
    future_submission_date = 0
    missing_submission_date = 0
    stale_submission = 0
    submission_dates: List[str] = []
    flagged_applications = 0
    gpas: List[float] = []
    quality_scores: List[int] = []
    quality_tier_counts: Dict[str, int] = {}
    readiness_scores: List[int] = []
    readiness_bucket_counts: Dict[str, int] = {}
    submission_age_values: List[int] = []
    submission_age_bucket_counts: Dict[str, int] = {}
    submission_recency_counts: Dict[str, int] = {}
    graduation_year_counts: Dict[str, int] = {}
    graduation_year_bucket_counts: Dict[str, int] = {}

    for app in apps:
        program_counts[app.program] = program_counts.get(app.program, 0) + 1
        if app.first_gen:
            first_gen_program_counts[app.program] = first_gen_program_counts.get(app.program, 0) + 1
        if app.referral_source:
            referral_source_counts[app.referral_source] = (
                referral_source_counts.get(app.referral_source, 0) + 1
            )
        if app.citizenship_status:
            citizenship_status_counts[app.citizenship_status] = (
                citizenship_status_counts.get(app.citizenship_status, 0) + 1
            )
        else:
            citizenship_status_counts["Missing"] = citizenship_status_counts.get("Missing", 0) + 1
        if app.school_type:
            school_type_counts[app.school_type] = school_type_counts.get(app.school_type, 0) + 1
        else:
            school_type_counts["Missing"] = school_type_counts.get("Missing", 0) + 1
        if app.gpa is not None:
            gpas.append(app.gpa)
            program_gpas.setdefault(app.program, []).append(app.gpa)
        if app.income_bracket:
            income_bracket_counts[app.income_bracket] = income_bracket_counts.get(app.income_bracket, 0) + 1
        if app.note_tags:
            for tag in app.note_tags:
                note_tag_counts[tag] = note_tag_counts.get(tag, 0) + 1
        if app.email:
            domain = email_domain(app.email)
            if domain:
                email_domain_counts[domain] = email_domain_counts.get(domain, 0) + 1
        email_domain_category_counts[app.email_domain_category] = (
            email_domain_category_counts.get(app.email_domain_category, 0) + 1
        )
        if app.phone_country:
            phone_country_counts[app.phone_country] = phone_country_counts.get(app.phone_country, 0) + 1
        elif not app.phone:
            phone_country_counts["missing"] = phone_country_counts.get("missing", 0) + 1
        else:
            phone_country_counts["invalid"] = phone_country_counts.get("invalid", 0) + 1
        contact_channel_counts[app.contact_channel] = (
            contact_channel_counts.get(app.contact_channel, 0) + 1
        )
        submission_time_bucket_counts[app.submission_time_bucket] = (
            submission_time_bucket_counts.get(app.submission_time_bucket, 0) + 1
        )
        review_status_counts[app.review_status] = review_status_counts.get(app.review_status, 0) + 1
        review_priority_counts[app.review_priority] = review_priority_counts.get(app.review_priority, 0) + 1
        flag_severity_counts[app.flag_severity] = flag_severity_counts.get(app.flag_severity, 0) + 1
        if "missing_applicant_id" in app.flags:
            missing_applicant_id += 1
        if "missing_name" in app.flags:
            missing_name += 1
        if "missing_email" in app.flags:
            missing_email += 1
        if "invalid_email" in app.flags:
            invalid_email += 1
        if "missing_phone" in app.flags:
            missing_phone += 1
        if "invalid_phone" in app.flags:
            invalid_phone += 1
        if "missing_program" in app.flags:
            missing_program += 1
        if "missing_school_type" in app.flags:
            missing_school_type += 1
        if "missing_referral_source" in app.flags:
            missing_referral_source += 1
        if "missing_income" in app.flags:
            missing_income += 1
        if "missing_citizenship_status" in app.flags:
            missing_citizenship_status += 1
        if "unrecognized_citizenship_status" in app.flags:
            unrecognized_citizenship_status += 1
        if "low_gpa" in app.flags:
            low_gpa += 1
        if "invalid_gpa" in app.flags:
            invalid_gpa += 1
        if "gpa_out_of_range" in app.flags:
            gpa_out_of_range += 1
        if "missing_graduation_year" in app.flags:
            missing_graduation_year += 1
        if "invalid_graduation_year" in app.flags:
            invalid_graduation_year += 1
        if "graduation_year_out_of_range" in app.flags:
            graduation_year_out_of_range += 1
        if app.first_gen:
            first_gen += 1
        if "invalid_submission_date" in app.flags:
            invalid_submission_date += 1
        if "future_submission_date" in app.flags:
            future_submission_date += 1
        if "missing_submission_date" in app.flags:
            missing_submission_date += 1
        if "stale_submission" in app.flags:
            stale_submission += 1
        if app.submission_date:
            submission_dates.append(app.submission_date)
            weekday = date.fromisoformat(app.submission_date).strftime("%A")
            submission_weekday_counts[weekday] = submission_weekday_counts.get(weekday, 0) + 1
            if app.submission_age_days is not None:
                submission_age_values.append(app.submission_age_days)
            if app.submission_age_bucket:
                submission_age_bucket_counts[app.submission_age_bucket] = (
                    submission_age_bucket_counts.get(app.submission_age_bucket, 0) + 1
                )
        submission_recency_counts[app.submission_recency] = submission_recency_counts.get(
            app.submission_recency, 0
        ) + 1
        if app.graduation_year is not None:
            year_key = str(app.graduation_year)
            graduation_year_counts[year_key] = graduation_year_counts.get(year_key, 0) + 1
        graduation_year_bucket_counts[app.graduation_year_bucket] = (
            graduation_year_bucket_counts.get(app.graduation_year_bucket, 0) + 1
        )
        if app.flags:
            flagged_applications += 1
        quality_scores.append(app.data_quality_score)
        tier = quality_tier(app.data_quality_score)
        quality_tier_counts[tier] = quality_tier_counts.get(tier, 0) + 1
        readiness_scores.append(app.readiness_score)
        readiness_bucket_counts[app.readiness_bucket] = readiness_bucket_counts.get(app.readiness_bucket, 0) + 1

    submission_dates.sort()
    submission_start = submission_dates[0] if submission_dates else None
    submission_end = submission_dates[-1] if submission_dates else None
    flagged_rate = round((flagged_applications / len(apps) * 100), 1) if apps else 0.0
    first_gen_rate = round((first_gen / len(apps) * 100), 1) if apps else 0.0
    gpa_avg = round(sum(gpas) / len(gpas), 2) if gpas else None
    gpa_min = min(gpas) if gpas else None
    gpa_max = max(gpas) if gpas else None
    program_gpa_avg: Dict[str, Optional[float]] = {}
    for program, values in program_gpas.items():
        program_gpa_avg[program] = round(sum(values) / len(values), 2) if values else None
    for program in program_counts:
        first_gen_program_counts.setdefault(program, 0)
    first_gen_program_rates: Dict[str, float] = {}
    for program, total in program_counts.items():
        first_gen_count = first_gen_program_counts.get(program, 0)
        first_gen_program_rates[program] = round((first_gen_count / total * 100), 1) if total else 0.0
    data_quality_avg = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None
    data_quality_min = min(quality_scores) if quality_scores else None
    data_quality_max = max(quality_scores) if quality_scores else None
    readiness_avg = round(sum(readiness_scores) / len(readiness_scores), 1) if readiness_scores else None
    readiness_min = min(readiness_scores) if readiness_scores else None
    readiness_max = max(readiness_scores) if readiness_scores else None
    submission_age_avg = (
        round(sum(submission_age_values) / len(submission_age_values), 1) if submission_age_values else None
    )
    submission_age_min = min(submission_age_values) if submission_age_values else None
    submission_age_max = max(submission_age_values) if submission_age_values else None

    return Summary(
        total_rows=len(apps),
        missing_applicant_id=missing_applicant_id,
        missing_name=missing_name,
        missing_email=missing_email,
        invalid_email=invalid_email,
        missing_phone=missing_phone,
        invalid_phone=invalid_phone,
        missing_program=missing_program,
        missing_school_type=missing_school_type,
        missing_referral_source=missing_referral_source,
        missing_income=missing_income,
        missing_citizenship_status=missing_citizenship_status,
        unrecognized_citizenship_status=unrecognized_citizenship_status,
        low_gpa=low_gpa,
        invalid_gpa=invalid_gpa,
        gpa_out_of_range=gpa_out_of_range,
        first_gen=first_gen,
        first_gen_rate=first_gen_rate,
        invalid_submission_date=invalid_submission_date,
        future_submission_date=future_submission_date,
        missing_submission_date=missing_submission_date,
        stale_submission=stale_submission,
        missing_graduation_year=missing_graduation_year,
        invalid_graduation_year=invalid_graduation_year,
        graduation_year_out_of_range=graduation_year_out_of_range,
        duplicate_email=duplicate_email,
        duplicate_applicant_id=duplicate_applicant_id,
        duplicate_phone=duplicate_phone,
        flagged_applications=flagged_applications,
        flagged_rate=flagged_rate,
        gpa_avg=gpa_avg,
        gpa_min=gpa_min,
        gpa_max=gpa_max,
        program_counts=program_counts,
        program_gpa_avg=program_gpa_avg,
        first_gen_program_counts=first_gen_program_counts,
        first_gen_program_rates=first_gen_program_rates,
        school_type_counts=school_type_counts,
        referral_source_counts=referral_source_counts,
        income_bracket_counts=income_bracket_counts,
        citizenship_status_counts=citizenship_status_counts,
        note_tag_counts=note_tag_counts,
        email_domain_counts=email_domain_counts,
        email_domain_category_counts=email_domain_category_counts,
        phone_country_counts=phone_country_counts,
        contact_channel_counts=contact_channel_counts,
        submission_weekday_counts=submission_weekday_counts,
        submission_time_bucket_counts=submission_time_bucket_counts,
        review_status_counts=review_status_counts,
        review_priority_counts=review_priority_counts,
        flag_severity_counts=flag_severity_counts,
        data_quality_avg=data_quality_avg,
        data_quality_min=data_quality_min,
        data_quality_max=data_quality_max,
        quality_tier_counts=quality_tier_counts,
        readiness_avg=readiness_avg,
        readiness_min=readiness_min,
        readiness_max=readiness_max,
        readiness_bucket_counts=readiness_bucket_counts,
        submission_age_avg=submission_age_avg,
        submission_age_min=submission_age_min,
        submission_age_max=submission_age_max,
        submission_age_bucket_counts=submission_age_bucket_counts,
        submission_recency_counts=submission_recency_counts,
        graduation_year_counts=graduation_year_counts,
        graduation_year_bucket_counts=graduation_year_bucket_counts,
        submission_start=submission_start,
        submission_end=submission_end,
    )


def write_json(apps: List[NormalizedApplication], path: Path) -> None:
    payload = [asdict(app) for app in apps]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_scorecard(scorecard: Scorecard, path: Path) -> None:
    path.write_text(json.dumps(asdict(scorecard), indent=2), encoding="utf-8")


def write_report(summary: Summary, path: Path) -> None:
    def format_pct(value: float) -> str:
        return f"{value:.1f}%"

    lines = [
        "# Intake Normalization Summary",
        "",
        f"Total applications: {summary.total_rows}",
        f"Missing applicant ID: {summary.missing_applicant_id}",
        f"Missing applicant name: {summary.missing_name}",
        f"Missing email: {summary.missing_email}",
        f"Invalid email: {summary.invalid_email}",
        f"Missing phone: {summary.missing_phone}",
        f"Invalid phone: {summary.invalid_phone}",
        f"Missing program: {summary.missing_program}",
        f"Missing school type: {summary.missing_school_type}",
        f"Missing referral source: {summary.missing_referral_source}",
        f"Missing income: {summary.missing_income}",
        f"Missing citizenship status: {summary.missing_citizenship_status}",
        f"Unrecognized citizenship status: {summary.unrecognized_citizenship_status}",
        f"Low GPA (<2.5): {summary.low_gpa}",
        f"Invalid GPA: {summary.invalid_gpa}",
        f"GPA out of range: {summary.gpa_out_of_range}",
        f"GPA average: {summary.gpa_avg if summary.gpa_avg is not None else 'n/a'}",
        f"GPA range: {summary.gpa_min if summary.gpa_min is not None else 'n/a'} to {summary.gpa_max if summary.gpa_max is not None else 'n/a'}",
        f"First-gen applicants: {summary.first_gen} ({format_pct(summary.first_gen_rate)})",
        f"Invalid submission date: {summary.invalid_submission_date}",
        f"Future submission date: {summary.future_submission_date}",
        f"Missing submission date: {summary.missing_submission_date}",
        f"Stale submissions (>= {STALE_SUBMISSION_DAYS} days): {summary.stale_submission}",
        f"Missing graduation year: {summary.missing_graduation_year}",
        f"Invalid graduation year: {summary.invalid_graduation_year}",
        f"Graduation year out of range: {summary.graduation_year_out_of_range}",
        f"Duplicate emails: {summary.duplicate_email}",
        f"Duplicate applicant IDs: {summary.duplicate_applicant_id}",
        f"Duplicate phones: {summary.duplicate_phone}",
        f"Flagged applications: {summary.flagged_applications} ({summary.flagged_rate}%)",
        f"Data quality average: {summary.data_quality_avg if summary.data_quality_avg is not None else 'n/a'}",
        f"Data quality range: {summary.data_quality_min if summary.data_quality_min is not None else 'n/a'} to {summary.data_quality_max if summary.data_quality_max is not None else 'n/a'}",
        f"Readiness average: {summary.readiness_avg if summary.readiness_avg is not None else 'n/a'}",
        f"Readiness range: {summary.readiness_min if summary.readiness_min is not None else 'n/a'} to {summary.readiness_max if summary.readiness_max is not None else 'n/a'}",
        f"Submission age average (days): {summary.submission_age_avg if summary.submission_age_avg is not None else 'n/a'}",
        f"Submission age range (days): {summary.submission_age_min if summary.submission_age_min is not None else 'n/a'} to {summary.submission_age_max if summary.submission_age_max is not None else 'n/a'}",
        f"Submission window: {summary.submission_start or 'n/a'} to {summary.submission_end or 'n/a'}",
        "",
        "## Data quality tiers",
    ]
    for tier, _ in QUALITY_TIERS:
        count = summary.quality_tier_counts.get(tier, 0)
        lines.append(f"- {tier.replace('_', ' ').title()}: {count}")
    lines.extend(
        [
            "",
            "## Readiness buckets",
        ]
    )
    for bucket, _ in READINESS_BUCKETS:
        count = summary.readiness_bucket_counts.get(bucket, 0)
        lines.append(f"- {bucket.replace('_', ' ').title()}: {count}")
    lines.extend(
        [
            "",
            "## Review readiness",
        ]
    )
    for status in REVIEW_STATUS_ORDER:
        count = summary.review_status_counts.get(status, 0)
        lines.append(f"- {status.replace('_', ' ').title()}: {count}")
    lines.extend(
        [
            "",
            "## Review priority",
        ]
    )
    for priority in REVIEW_PRIORITY_ORDER:
        count = summary.review_priority_counts.get(priority, 0)
        lines.append(f"- {priority.replace('_', ' ').title()}: {count}")
    lines.extend(["", "## Flag severity"])
    for severity in FLAG_SEVERITY_ORDER:
        count = summary.flag_severity_counts.get(severity, 0)
        lines.append(f"- {severity.replace('_', ' ').title()}: {count}")
    lines.extend(["", "## Applications by program"])
    for program, count in sorted(summary.program_counts.items()):
        lines.append(f"- {program}: {count}")
    lines.append("")
    lines.append("## Applications by school type")
    if summary.school_type_counts:
        for school_type in SCHOOL_TYPE_ORDER:
            count = summary.school_type_counts.get(school_type)
            if count is not None:
                lines.append(f"- {school_type}: {count}")
        for school_type, count in sorted(summary.school_type_counts.items()):
            if school_type in SCHOOL_TYPE_ORDER:
                continue
            lines.append(f"- {school_type}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## GPA by program")
    for program, avg in sorted(summary.program_gpa_avg.items()):
        lines.append(f"- {program}: {avg if avg is not None else 'n/a'}")
    lines.append("")
    lines.append("## First-gen mix by program")
    if summary.program_counts:
        for program in sorted(summary.program_counts.keys()):
            first_gen_count = summary.first_gen_program_counts.get(program, 0)
            total = summary.program_counts.get(program, 0)
            rate = summary.first_gen_program_rates.get(program, 0.0)
            lines.append(f"- {program}: {first_gen_count}/{total} ({format_pct(rate)})")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Applications by income bracket")
    for bracket, count in sorted(summary.income_bracket_counts.items()):
        lines.append(f"- {bracket}: {count}")
    lines.append("")
    lines.append("## Applications by referral source")
    if summary.referral_source_counts:
        for source, count in sorted(summary.referral_source_counts.items()):
            lines.append(f"- {source}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Citizenship status mix")
    if summary.citizenship_status_counts:
        for status in CITIZENSHIP_STATUS_ORDER:
            count = summary.citizenship_status_counts.get(status)
            if count is not None:
                lines.append(f"- {status}: {count}")
        for status, count in sorted(summary.citizenship_status_counts.items()):
            if status in CITIZENSHIP_STATUS_ORDER:
                continue
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Eligibility note tags")
    if summary.note_tag_counts:
        for tag, count in sorted(summary.note_tag_counts.items()):
            lines.append(f"- {tag.replace('_', ' ').title()}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Top email domains")
    if summary.email_domain_counts:
        top_domains = sorted(
            summary.email_domain_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]
        for domain, count in top_domains:
            lines.append(f"- {domain}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Email domain categories")
    if summary.email_domain_category_counts:
        for category in EMAIL_DOMAIN_CATEGORY_ORDER:
            count = summary.email_domain_category_counts.get(category, 0)
            lines.append(f"- {category.replace('_', ' ').title()}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Phone country mix")
    if summary.phone_country_counts:
        for country, count in sorted(summary.phone_country_counts.items()):
            lines.append(f"- {country}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Contact channel mix")
    if summary.contact_channel_counts:
        for channel in CONTACT_CHANNEL_ORDER:
            count = summary.contact_channel_counts.get(channel, 0)
            lines.append(f"- {channel.replace('_', ' ').title()}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Submissions by weekday")
    if summary.submission_weekday_counts:
        for weekday in WEEKDAY_ORDER:
            count = summary.submission_weekday_counts.get(weekday, 0)
            lines.append(f"- {weekday}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Submissions by time of day")
    if summary.submission_time_bucket_counts:
        for bucket in SUBMISSION_TIME_BUCKET_ORDER:
            count = summary.submission_time_bucket_counts.get(bucket, 0)
            label = bucket.replace("_", " ").title()
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Submission age buckets")
    if summary.submission_age_bucket_counts:
        for bucket, _ in SUBMISSION_AGE_BUCKETS:
            count = summary.submission_age_bucket_counts.get(bucket, 0)
            lines.append(f"- {bucket}: {count}")
        future_count = summary.submission_age_bucket_counts.get("future")
        if future_count:
            lines.append(f"- Future: {future_count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Submission recency")
    if summary.submission_recency_counts:
        for bucket, _ in SUBMISSION_RECENCY_BUCKETS:
            count = summary.submission_recency_counts.get(bucket, 0)
            lines.append(f"- {bucket.title()}: {count}")
        missing_count = summary.submission_recency_counts.get("missing")
        if missing_count:
            lines.append(f"- Missing: {missing_count}")
        future_count = summary.submission_recency_counts.get("future")
        if future_count:
            lines.append(f"- Future: {future_count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Graduation year counts")
    if summary.graduation_year_counts:
        for year, count in sorted(summary.graduation_year_counts.items()):
            lines.append(f"- {year}: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Graduation year buckets")
    if summary.graduation_year_bucket_counts:
        for bucket in GRADUATION_YEAR_BUCKETS:
            count = summary.graduation_year_bucket_counts.get(bucket, 0)
            lines.append(f"- {bucket.replace('_', ' ').title()}: {count}")
    else:
        lines.append("- n/a")
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
        "missing_phone": "Missing phone",
        "invalid_phone": "Invalid phone",
        "missing_program": "Missing program",
        "missing_school_type": "Missing school type",
        "missing_referral_source": "Missing referral source",
        "missing_income": "Missing income bracket",
        "missing_citizenship_status": "Missing citizenship status",
        "unrecognized_citizenship_status": "Unrecognized citizenship status",
        "low_gpa": "Low GPA",
        "invalid_gpa": "Invalid GPA format",
        "gpa_out_of_range": "GPA out of range",
        "missing_graduation_year": "Missing graduation year",
        "invalid_graduation_year": "Invalid graduation year",
        "graduation_year_out_of_range": "Graduation year out of range",
        "invalid_submission_date": "Invalid submission date",
        "future_submission_date": "Submission date in future",
        "missing_submission_date": "Missing submission date",
        "stale_submission": f"Submission older than {STALE_SUBMISSION_DAYS} days",
        "duplicate_email": "Duplicate email",
        "duplicate_applicant_id": "Duplicate applicant ID",
        "duplicate_phone": "Duplicate phone",
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
                "phone": app.phone or "",
                "phone_normalized": app.phone_normalized or "",
                "phone_country": app.phone_country or "",
                "program": app.program,
                "school_type": app.school_type or "",
                "citizenship_status": app.citizenship_status or "",
                "referral_source": app.referral_source or "",
                "submission_date": app.submission_date or "",
                "submission_age_days": app.submission_age_days if app.submission_age_days is not None else "",
                "submission_age_bucket": app.submission_age_bucket or "",
                "submission_recency": app.submission_recency,
                "graduation_year": app.graduation_year if app.graduation_year is not None else "",
                "graduation_year_bucket": app.graduation_year_bucket,
                "flags": "; ".join(app.flags),
                "flag_severity": app.flag_severity,
                "review_status": app.review_status,
                "review_priority": app.review_priority,
                "data_quality_score": app.data_quality_score,
                "quality_tier": quality_tier(app.data_quality_score),
                "readiness_score": app.readiness_score,
                "readiness_bucket": app.readiness_bucket,
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
                "phone",
                "phone_normalized",
                "phone_country",
                "program",
                "school_type",
                "citizenship_status",
                "referral_source",
                "submission_date",
                "submission_age_days",
                "submission_age_bucket",
                "submission_recency",
                "graduation_year",
                "graduation_year_bucket",
                "flags",
                "flag_severity",
                "review_status",
                "review_priority",
                "data_quality_score",
                "quality_tier",
                "readiness_score",
                "readiness_bucket",
                "follow_up_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def recommended_action(flags: List[str]) -> str:
    if not flags:
        return "Ready for review"
    if any(flag in {"missing_email", "missing_phone"} for flag in flags):
        return "Request missing contact details"
    if any(flag in {"invalid_email", "invalid_phone"} for flag in flags):
        return "Verify contact information"
    if "missing_submission_date" in flags or "invalid_submission_date" in flags:
        return "Confirm submission date"
    if "missing_program" in flags:
        return "Confirm program selection"
    if "missing_school_type" in flags:
        return "Capture school type"
    if "missing_citizenship_status" in flags or "unrecognized_citizenship_status" in flags:
        return "Confirm citizenship status"
    if "missing_referral_source" in flags:
        return "Capture referral source"
    if any(flag in {"duplicate_email", "duplicate_applicant_id", "duplicate_phone"} for flag in flags):
        return "Resolve possible duplicate"
    if any(flag in {"low_gpa", "invalid_gpa", "gpa_out_of_range"} for flag in flags):
        return "Review academic metrics"
    if any(flag in {"missing_graduation_year", "invalid_graduation_year"} for flag in flags):
        return "Confirm graduation year"
    if "graduation_year_out_of_range" in flags:
        return "Verify graduation year range"
    if "stale_submission" in flags:
        return "Check submission follow-up"
    return "Review application notes"


def write_followup_queue(apps: List[NormalizedApplication], path: Path) -> None:
    priority_rank = {priority: index for index, priority in enumerate(REVIEW_PRIORITY_ORDER)}

    def sort_key(app: NormalizedApplication) -> Tuple[int, int, str]:
        rank = priority_rank.get(app.review_priority, len(priority_rank))
        age_days = app.submission_age_days if app.submission_age_days is not None else -1
        return (rank, -age_days, app.name.lower())

    rows = []
    for app in sorted(apps, key=sort_key):
        if app.review_priority == "ready" and not app.flags:
            continue
        rows.append(
            {
                "applicant_id": app.applicant_id,
                "name": app.name,
                "email": app.email or "",
                "phone": app.phone or "",
                "program": app.program,
                "school_type": app.school_type or "",
                "citizenship_status": app.citizenship_status or "",
                "review_status": app.review_status,
                "review_priority": app.review_priority,
                "flag_severity": app.flag_severity,
                "data_quality_score": app.data_quality_score,
                "readiness_score": app.readiness_score,
                "submission_date": app.submission_date or "",
                "submission_age_days": app.submission_age_days if app.submission_age_days is not None else "",
                "submission_recency": app.submission_recency,
                "graduation_year": app.graduation_year if app.graduation_year is not None else "",
                "follow_up_reason": follow_up_reason(app.flags),
                "recommended_action": recommended_action(app.flags),
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "applicant_id",
                "name",
                "email",
                "phone",
                "program",
                "school_type",
                "citizenship_status",
                "review_status",
                "review_priority",
                "flag_severity",
                "data_quality_score",
                "readiness_score",
                "submission_date",
                "submission_age_days",
                "submission_recency",
                "graduation_year",
                "follow_up_reason",
                "recommended_action",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def build_scorecard(apps: List[NormalizedApplication], summary: Summary) -> Scorecard:
    flag_totals: Dict[str, int] = {}
    for app in apps:
        for flag in app.flags:
            flag_totals[flag] = flag_totals.get(flag, 0) + 1
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
        first_gen_program_counts=summary.first_gen_program_counts,
        first_gen_program_rates=summary.first_gen_program_rates,
        school_type_counts=summary.school_type_counts,
        referral_source_counts=summary.referral_source_counts,
        income_bracket_counts=summary.income_bracket_counts,
        email_domain_counts=dict(
            sorted(summary.email_domain_counts.items(), key=lambda item: item[1], reverse=True)
        ),
        email_domain_category_counts=summary.email_domain_category_counts,
        phone_country_counts=summary.phone_country_counts,
        contact_channel_counts=summary.contact_channel_counts,
        note_tag_counts=summary.note_tag_counts,
        citizenship_status_counts=summary.citizenship_status_counts,
        submission_weekday_counts=summary.submission_weekday_counts,
        submission_time_bucket_counts=summary.submission_time_bucket_counts,
        review_status_counts=summary.review_status_counts,
        review_priority_counts=summary.review_priority_counts,
        flag_severity_counts=summary.flag_severity_counts,
        data_quality_avg=summary.data_quality_avg,
        data_quality_min=summary.data_quality_min,
        data_quality_max=summary.data_quality_max,
        quality_tier_counts=summary.quality_tier_counts,
        readiness_avg=summary.readiness_avg,
        readiness_min=summary.readiness_min,
        readiness_max=summary.readiness_max,
        readiness_bucket_counts=summary.readiness_bucket_counts,
        gpa_avg=summary.gpa_avg,
        gpa_min=summary.gpa_min,
        gpa_max=summary.gpa_max,
        first_gen_rate=summary.first_gen_rate,
        submission_age_avg=summary.submission_age_avg,
        submission_age_min=summary.submission_age_min,
        submission_age_max=summary.submission_age_max,
        submission_age_bucket_counts=summary.submission_age_bucket_counts,
        submission_recency_counts=summary.submission_recency_counts,
        graduation_year_counts=summary.graduation_year_counts,
        graduation_year_bucket_counts=summary.graduation_year_bucket_counts,
        submission_start=summary.submission_start,
        submission_end=summary.submission_end,
    )


def run(
    input_path: Path,
    out_path: Path,
    report_path: Path,
    issues_path: Optional[Path],
    scorecard_path: Optional[Path],
    queue_path: Optional[Path],
) -> Tuple[int, int]:
    rows = read_applications(input_path)
    apps = [normalize_row(row) for row in rows]
    duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
    update_review_status(apps)
    summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)
    ensure_parent(out_path)
    ensure_parent(report_path)
    write_json(apps, out_path)
    write_report(summary, report_path)
    if issues_path:
        ensure_parent(issues_path)
        write_issues(apps, issues_path)
    if queue_path:
        ensure_parent(queue_path)
        write_followup_queue(apps, queue_path)
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
    queue_path: Optional[Path],
    db_url: Optional[str],
    batch_label: Optional[str],
) -> Tuple[int, int, str]:
    rows = read_applications(input_path)
    apps = [normalize_row(row) for row in rows]
    duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
    update_review_status(apps)
    summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)
    ensure_parent(out_path)
    ensure_parent(report_path)
    write_json(apps, out_path)
    write_report(summary, report_path)
    if issues_path:
        ensure_parent(issues_path)
        write_issues(apps, issues_path)
    if queue_path:
        ensure_parent(queue_path)
        write_followup_queue(apps, queue_path)
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
    parser.add_argument("--queue", help="Optional path to write follow-up queue CSV")
    parser.add_argument("--scorecard", help="Optional path to write scorecard JSON")
    parser.add_argument("--db", action="store_true", help="Also export normalized data to Postgres")
    parser.add_argument("--db-url", help="Optional database URL override")
    parser.add_argument("--batch-label", help="Optional label for the ingestion batch")
    args = parser.parse_args()

    issues_path = Path(args.issues) if args.issues else None
    queue_path = Path(args.queue) if args.queue else None
    scorecard_path = Path(args.scorecard) if args.scorecard else None
    if args.db:
        count, programs, batch_id = run_with_db(
            Path(args.input),
            Path(args.out),
            Path(args.report),
            issues_path,
            scorecard_path,
            queue_path,
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
            queue_path,
        )
        print(f"Normalized {count} applications across {programs} programs.")


if __name__ == "__main__":
    main()
