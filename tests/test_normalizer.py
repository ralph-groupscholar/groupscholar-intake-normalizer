import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from normalizer import (
    apply_duplicate_flags,
    build_scorecard,
    build_summary,
    normalize_row,
    submission_recency,
    update_review_status,
)


class NormalizerSummaryTest(unittest.TestCase):
    def test_email_domain_and_weekday_counts(self):
        rows = [
            {
                "applicant_id": "A-1",
                "name": "Alex Example",
                "email": "Alex@Example.com",
                "program": "STEM Scholars",
                "referral_source": "School Counselor",
                "gpa": "3.4",
                "income_bracket": "<=40k",
                "submission_date": "2026-01-20",
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-2",
                "name": "Riley Scholar",
                "email": "riley@school.edu",
                "program": "Arts Catalyst",
                "referral_source": "Instagram",
                "gpa": "3.8",
                "income_bracket": "70k-100k",
                "submission_date": "2026-01-21",
                "first_gen": "no",
                "eligibility_notes": "All docs complete",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email=0, duplicate_applicant_id=0)

        self.assertEqual(summary.email_domain_counts.get("example.com"), 1)
        self.assertEqual(summary.email_domain_counts.get("school.edu"), 1)
        self.assertEqual(summary.email_domain_category_counts.get("commercial"), 1)
        self.assertEqual(summary.email_domain_category_counts.get("education"), 1)

        expected_weekdays = {
            date.fromisoformat("2026-01-20").strftime("%A"): 1,
            date.fromisoformat("2026-01-21").strftime("%A"): 1,
        }
        for weekday, count in expected_weekdays.items():
            self.assertEqual(summary.submission_weekday_counts.get(weekday), count)

        self.assertEqual(summary.flag_severity_counts.get("clean"), 2)
        expected_recency = submission_recency(apps[0].submission_age_days)
        self.assertEqual(summary.submission_recency_counts.get(expected_recency), 2)
        self.assertEqual(summary.referral_source_counts.get("School Counselor"), 1)
        self.assertEqual(summary.referral_source_counts.get("Social Media"), 1)

        scorecard = build_scorecard(apps, summary)
        self.assertEqual(scorecard.email_domain_counts.get("example.com"), 1)
        self.assertEqual(scorecard.email_domain_category_counts.get("commercial"), 1)
        self.assertEqual(scorecard.submission_weekday_counts.get(list(expected_weekdays.keys())[0]), 1)
        self.assertEqual(scorecard.flag_severity_counts.get("clean"), 2)
        self.assertEqual(scorecard.submission_recency_counts.get(expected_recency), 2)
        self.assertEqual(scorecard.referral_source_counts.get("School Counselor"), 1)
        self.assertEqual(scorecard.referral_source_counts.get("Social Media"), 1)

    def test_missing_submission_date_is_flagged(self):
        row = {
            "applicant_id": "A-3",
            "name": "Sam MissingDate",
            "email": "sam@example.org",
            "program": "Health Futures",
            "referral_source": "",
            "gpa": "3.2",
            "income_bracket": "40k-70k",
            "submission_date": "",
            "first_gen": "no",
            "eligibility_notes": "",
        }
        app = normalize_row(row)
        self.assertIn("missing_submission_date", app.flags)
        self.assertIn("missing_referral_source", app.flags)
        update_review_status([app])
        self.assertEqual(app.review_status, "needs_review")
        self.assertEqual(app.review_priority, "medium")

        summary = build_summary([app], duplicate_email=0, duplicate_applicant_id=0)
        self.assertEqual(summary.missing_submission_date, 1)
        self.assertEqual(summary.missing_referral_source, 1)

    def test_submission_recency_counts(self):
        today = date.today()
        rows = [
            {
                "applicant_id": "A-10",
                "name": "Fresh Intake",
                "email": "fresh@example.com",
                "program": "STEM Scholars",
                "referral_source": "Website",
                "gpa": "3.5",
                "income_bracket": "<=40k",
                "submission_date": today.isoformat(),
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-11",
                "name": "Stale Intake",
                "email": "stale@example.com",
                "program": "Arts Catalyst",
                "referral_source": "Teacher",
                "gpa": "3.1",
                "income_bracket": "40k-70k",
                "submission_date": (today - timedelta(days=40)).isoformat(),
                "first_gen": "no",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-12",
                "name": "Missing Intake",
                "email": "missing@example.com",
                "program": "Health Futures",
                "referral_source": "",
                "gpa": "3.7",
                "income_bracket": "70k-100k",
                "submission_date": "",
                "first_gen": "no",
                "eligibility_notes": "",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email=0, duplicate_applicant_id=0)

        self.assertEqual(summary.submission_recency_counts.get("fresh"), 1)
        self.assertEqual(summary.submission_recency_counts.get("stale"), 1)
        self.assertEqual(summary.submission_recency_counts.get("missing"), 1)


if __name__ == "__main__":
    unittest.main()
