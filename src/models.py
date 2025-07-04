from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


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
    missing_name: int
    missing_email: int
    invalid_email: int
    missing_program: int
    missing_income: int
    low_gpa: int
    invalid_gpa: int
    gpa_out_of_range: int
    first_gen: int
    invalid_submission_date: int
    future_submission_date: int
    duplicate_email: int
    duplicate_applicant_id: int
    flagged_applications: int
    flagged_rate: float
    gpa_avg: Optional[float]
    gpa_min: Optional[float]
    gpa_max: Optional[float]
    program_counts: Dict[str, int]
    program_gpa_avg: Dict[str, Optional[float]]
    income_bracket_counts: Dict[str, int]
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
    income_bracket_counts: Dict[str, int]
    email_domain_counts: Dict[str, int]
    gpa_avg: Optional[float]
    gpa_min: Optional[float]
    gpa_max: Optional[float]
    submission_start: Optional[str]
    submission_end: Optional[str]
