import csv
import sys
import tempfile
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
    write_followup_queue,
)


class NormalizerSummaryTest(unittest.TestCase):
    def test_email_domain_and_weekday_counts(self):
        rows = [
            {
                "applicant_id": "A-1",
                "name": "Alex Example",
                "email": "Alex@Example.com",
                "phone": "312-555-0101",
                "program": "STEM Scholars",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "School Counselor",
                "gpa": "3.4",
                "income_bracket": "<=40k",
                "submission_date": "2026-01-20",
                "graduation_year": "2026",
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-2",
                "name": "Riley Scholar",
                "email": "riley@school.edu",
                "phone": "+44 20 7946 0958",
                "program": "Arts Catalyst",
                "school_type": "Private",
                "citizenship_status": "International",
                "referral_source": "Instagram",
                "gpa": "3.8",
                "income_bracket": "70k-100k",
                "submission_date": "2026-01-21",
                "graduation_year": "2027",
                "first_gen": "no",
                "eligibility_notes": "All docs complete",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)

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
        self.assertEqual(summary.school_type_counts.get("Public"), 1)
        self.assertEqual(summary.school_type_counts.get("Private"), 1)
        self.assertEqual(summary.citizenship_status_counts.get("US Citizen"), 1)
        self.assertEqual(summary.citizenship_status_counts.get("International"), 1)
        self.assertEqual(summary.first_gen_rate, 50.0)
        self.assertEqual(summary.first_gen_program_counts.get("STEM Scholars"), 1)
        self.assertEqual(summary.first_gen_program_counts.get("Arts Catalyst"), 0)
        self.assertEqual(summary.first_gen_program_rates.get("STEM Scholars"), 100.0)
        self.assertEqual(summary.first_gen_program_rates.get("Arts Catalyst"), 0.0)
        self.assertEqual(summary.graduation_year_counts.get("2026"), 1)
        self.assertEqual(summary.graduation_year_counts.get("2027"), 1)
        self.assertEqual(summary.graduation_year_bucket_counts.get("current"), 1)
        self.assertEqual(summary.graduation_year_bucket_counts.get("next_year"), 1)

        scorecard = build_scorecard(apps, summary)
        self.assertEqual(scorecard.email_domain_counts.get("example.com"), 1)
        self.assertEqual(scorecard.email_domain_category_counts.get("commercial"), 1)
        self.assertEqual(scorecard.submission_weekday_counts.get(list(expected_weekdays.keys())[0]), 1)
        self.assertEqual(scorecard.flag_severity_counts.get("clean"), 2)
        self.assertEqual(scorecard.submission_recency_counts.get(expected_recency), 2)
        self.assertEqual(scorecard.referral_source_counts.get("School Counselor"), 1)
        self.assertEqual(scorecard.referral_source_counts.get("Social Media"), 1)
        self.assertEqual(scorecard.school_type_counts.get("Public"), 1)
        self.assertEqual(scorecard.school_type_counts.get("Private"), 1)
        self.assertEqual(scorecard.citizenship_status_counts.get("US Citizen"), 1)
        self.assertEqual(scorecard.citizenship_status_counts.get("International"), 1)
        self.assertEqual(scorecard.first_gen_rate, 50.0)
        self.assertEqual(scorecard.first_gen_program_counts.get("STEM Scholars"), 1)
        self.assertEqual(scorecard.first_gen_program_counts.get("Arts Catalyst"), 0)
        self.assertEqual(scorecard.first_gen_program_rates.get("STEM Scholars"), 100.0)
        self.assertEqual(scorecard.first_gen_program_rates.get("Arts Catalyst"), 0.0)
        self.assertEqual(scorecard.graduation_year_counts.get("2026"), 1)
        self.assertEqual(scorecard.graduation_year_counts.get("2027"), 1)
        self.assertEqual(scorecard.graduation_year_bucket_counts.get("current"), 1)
        self.assertEqual(scorecard.graduation_year_bucket_counts.get("next_year"), 1)

    def test_phone_normalization_and_country_counts(self):
        rows = [
            {
                "applicant_id": "A-20",
                "name": "Alex Phone",
                "email": "alex.phone@example.com",
                "phone": "(312) 555-0101",
                "program": "STEM Scholars",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.5",
                "income_bracket": "<=40k",
                "submission_date": "2026-01-22",
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-21",
                "name": "Rina Phone",
                "email": "rina.phone@example.com",
                "phone": "+91 98765 43210",
                "program": "Arts Catalyst",
                "school_type": "International",
                "citizenship_status": "Permanent Resident",
                "referral_source": "Teacher",
                "gpa": "3.2",
                "income_bracket": "40k-70k",
                "submission_date": "2026-01-22",
                "first_gen": "no",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-22",
                "name": "Missing Phone",
                "email": "missing.phone@example.com",
                "phone": "",
                "program": "Health Futures",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.0",
                "income_bracket": "70k-100k",
                "submission_date": "2026-01-22",
                "first_gen": "no",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-23",
                "name": "Bad Phone",
                "email": "bad.phone@example.com",
                "phone": "not-a-number",
                "program": "Health Futures",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.1",
                "income_bracket": "70k-100k",
                "submission_date": "2026-01-22",
                "first_gen": "no",
                "eligibility_notes": "",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)

        self.assertEqual(apps[0].phone_normalized, "+13125550101")
        self.assertEqual(apps[0].phone_country, "US/Canada")
        self.assertEqual(apps[1].phone_normalized, "+919876543210")
        self.assertEqual(apps[1].phone_country, "India")
        self.assertIn("missing_phone", apps[2].flags)
        self.assertIn("invalid_phone", apps[3].flags)
        self.assertEqual(summary.missing_phone, 1)
        self.assertEqual(summary.invalid_phone, 1)
        self.assertEqual(summary.phone_country_counts.get("US/Canada"), 1)
        self.assertEqual(summary.phone_country_counts.get("India"), 1)
        self.assertEqual(summary.contact_channel_counts.get("email_and_phone"), 2)
        self.assertEqual(summary.contact_channel_counts.get("email_only"), 2)

    def test_missing_submission_date_is_flagged(self):
        row = {
            "applicant_id": "A-3",
            "name": "Sam MissingDate",
            "email": "sam@example.org",
            "program": "Health Futures",
            "school_type": "Public",
            "citizenship_status": "US Citizen",
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

        summary = build_summary([app], duplicate_email=0, duplicate_applicant_id=0, duplicate_phone=0)
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
                "school_type": "Public",
                "citizenship_status": "US Citizen",
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
                "school_type": "Private",
                "citizenship_status": "Permanent Resident",
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
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "",
                "gpa": "3.7",
                "income_bracket": "70k-100k",
                "submission_date": "",
                "first_gen": "no",
                "eligibility_notes": "",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)

        self.assertEqual(summary.submission_recency_counts.get("fresh"), 1)
        self.assertEqual(summary.submission_recency_counts.get("stale"), 1)
        self.assertEqual(summary.submission_recency_counts.get("missing"), 1)

    def test_duplicate_phone_flags(self):
        rows = [
            {
                "applicant_id": "A-30",
                "name": "Casey Dup",
                "email": "casey.dup@example.com",
                "phone": "312-555-0101",
                "program": "STEM Scholars",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.3",
                "income_bracket": "<=40k",
                "submission_date": "2026-01-20",
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-31",
                "name": "Jordan Dup",
                "email": "jordan.dup@example.com",
                "phone": "+1 (312) 555-0101",
                "program": "Arts Catalyst",
                "school_type": "Private",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.4",
                "income_bracket": "40k-70k",
                "submission_date": "2026-01-20",
                "first_gen": "no",
                "eligibility_notes": "",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        duplicate_email, duplicate_applicant_id, duplicate_phone = apply_duplicate_flags(apps)
        update_review_status(apps)
        summary = build_summary(apps, duplicate_email, duplicate_applicant_id, duplicate_phone)

        self.assertIn("duplicate_phone", apps[0].flags)
        self.assertIn("duplicate_phone", apps[1].flags)
        self.assertEqual(summary.duplicate_phone, 1)

    def test_followup_queue_output(self):
        rows = [
            {
                "applicant_id": "A-100",
                "name": "Priority Missing Email",
                "email": "",
                "phone": "312-555-0101",
                "program": "STEM Scholars",
                "school_type": "Public",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "3.1",
                "income_bracket": "<=40k",
                "submission_date": "2026-01-15",
                "graduation_year": "2026",
                "first_gen": "yes",
                "eligibility_notes": "",
            },
            {
                "applicant_id": "A-101",
                "name": "Low Priority",
                "email": "low@example.com",
                "phone": "312-555-0102",
                "program": "Arts Catalyst",
                "school_type": "Private",
                "citizenship_status": "US Citizen",
                "referral_source": "Website",
                "gpa": "2.4",
                "income_bracket": "40k-70k",
                "submission_date": "2026-01-20",
                "graduation_year": "2027",
                "first_gen": "no",
                "eligibility_notes": "",
            },
        ]
        apps = [normalize_row(row) for row in rows]
        apply_duplicate_flags(apps)
        update_review_status(apps)

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "queue.csv"
            write_followup_queue(apps, queue_path)
            with queue_path.open(encoding="utf-8", newline="") as handle:
                data = list(csv.DictReader(handle))

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["review_priority"], "high")
        self.assertEqual(data[0]["applicant_id"], "A-100")
        self.assertTrue(data[0]["recommended_action"])


if __name__ == "__main__":
    unittest.main()
