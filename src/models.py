from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class NormalizedApplication:
    applicant_id: str
    name: str
    email: Optional[str]
    email_domain_category: str
    program: str
    referral_source: Optional[str]
    gpa: Optional[float]
    income_bracket: Optional[str]
    submission_date: Optional[str]
    submission_age_days: Optional[int]
    submission_age_bucket: Optional[str]
    submission_recency: str
    first_gen: bool
    eligibility_notes: Optional[str]
    note_tags: List[str]
    flags: List[str]
    flag_severity: str
    review_status: str
    review_priority: str
    data_quality_score: int
    readiness_score: int
    readiness_bucket: str


@dataclass
class Summary:
    total_rows: int
    missing_applicant_id: int
    missing_name: int
    missing_email: int
    invalid_email: int
    missing_program: int
    missing_referral_source: int
    missing_income: int
    low_gpa: int
    invalid_gpa: int
    gpa_out_of_range: int
    first_gen: int
    invalid_submission_date: int
    future_submission_date: int
    missing_submission_date: int
    stale_submission: int
    duplicate_email: int
    duplicate_applicant_id: int
    flagged_applications: int
    flagged_rate: float
    gpa_avg: Optional[float]
    gpa_min: Optional[float]
    gpa_max: Optional[float]
    program_counts: Dict[str, int]
    program_gpa_avg: Dict[str, Optional[float]]
    referral_source_counts: Dict[str, int]
    income_bracket_counts: Dict[str, int]
    note_tag_counts: Dict[str, int]
    email_domain_counts: Dict[str, int]
    email_domain_category_counts: Dict[str, int]
    submission_weekday_counts: Dict[str, int]
    review_status_counts: Dict[str, int]
    review_priority_counts: Dict[str, int]
    flag_severity_counts: Dict[str, int]
    data_quality_avg: Optional[float]
    data_quality_min: Optional[int]
    data_quality_max: Optional[int]
    quality_tier_counts: Dict[str, int]
    readiness_avg: Optional[float]
    readiness_min: Optional[int]
    readiness_max: Optional[int]
    readiness_bucket_counts: Dict[str, int]
    submission_age_avg: Optional[float]
    submission_age_min: Optional[int]
    submission_age_max: Optional[int]
    submission_age_bucket_counts: Dict[str, int]
    submission_recency_counts: Dict[str, int]
    submission_start: Optional[str]
    submission_end: Optional[str]


@dataclass
class Scorecard:
    total_rows: int
    flagged_applications: int
    flagged_rate: float
    flag_rates: Dict[str, float]
    program_counts: Dict[str, int]
    program_gpa_avg: Dict[str, Optional[float]]
    referral_source_counts: Dict[str, int]
    income_bracket_counts: Dict[str, int]
    email_domain_counts: Dict[str, int]
    note_tag_counts: Dict[str, int]
    submission_weekday_counts: Dict[str, int]
    review_status_counts: Dict[str, int]
    review_priority_counts: Dict[str, int]
    flag_severity_counts: Dict[str, int]
    email_domain_category_counts: Dict[str, int]
    data_quality_avg: Optional[float]
    data_quality_min: Optional[int]
    data_quality_max: Optional[int]
    quality_tier_counts: Dict[str, int]
    readiness_avg: Optional[float]
    readiness_min: Optional[int]
    readiness_max: Optional[int]
    readiness_bucket_counts: Dict[str, int]
    gpa_avg: Optional[float]
    gpa_min: Optional[float]
    gpa_max: Optional[float]
    submission_age_avg: Optional[float]
    submission_age_min: Optional[int]
    submission_age_max: Optional[int]
    submission_age_bucket_counts: Dict[str, int]
    submission_recency_counts: Dict[str, int]
    submission_start: Optional[str]
    submission_end: Optional[str]
