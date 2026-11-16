import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import clean_up, is_cs_role, is_early_career, years_of_experience

NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)


def posting(title, description):
    return {
        "title": title,
        "location": {"name": "Hawthorne, CA"},
        "absolute_url": "https://jobs.example/1",
        "content": f"<p>{description}</p>",
    }


class YearsOfExperienceTests(unittest.TestCase):
    def test_reads_common_phrasings(self):
        cases = {
            "3+ years of experience in Python": 3,
            "2-4 years of professional software experience": 2,
            "Minimum 5 years experience": 5,
            "3 to 5 years of industry experience": 3,
            "0\u20132 years of relevant work experience": 0,
            "7 years of software development experience required": 7,
        }
        for text, years in cases.items():
            with self.subTest(text=text):
                self.assertEqual(years_of_experience(text), years)

    def test_smallest_number_wins(self):
        self.assertEqual(years_of_experience("5+ years of experience; 1+ years of experience with AWS"), 1)

    def test_no_experience_requirement(self):
        self.assertIsNone(years_of_experience("Founded 10 years ago. Bachelor's degree in CS."))
        self.assertIsNone(years_of_experience(""))


class EarlyCareerTests(unittest.TestCase):
    def test_plain_title_uses_the_description(self):
        self.assertTrue(is_early_career("Software Engineer", "BS in CS. 0-2 years of experience."))
        self.assertTrue(is_early_career("Software Engineer", "BS in Computer Science."))
        self.assertFalse(is_early_career("Software Engineer", "5+ years of experience building APIs."))

    def test_early_career_title_always_counts(self):
        self.assertTrue(is_early_career("Software Engineer, New Grad", "3+ years of experience preferred"))
        self.assertTrue(is_early_career("Software Engineer Intern", "5+ years of experience"))

    def test_mid_level_titles_are_dropped(self):
        self.assertFalse(is_cs_role("Software Engineer II"))
        self.assertFalse(is_cs_role("Mid-Level Backend Engineer"))
        self.assertTrue(is_cs_role("Software Engineer I"))
        self.assertTrue(is_cs_role("Junior Developer"))

    def test_hardware_company_engineering_roles_are_dropped(self):
        for title in ["Supplier Development Engineer - Starlink", "Electromagnetic Effects Test Engineer",
                      "Gateway Site Development Engineer", "Structures Engineer"]:
            with self.subTest(title=title):
                self.assertFalse(is_cs_role(title))
        for title in ["Software Engineer - Hardware Test & Automation", "Site Reliability Engineer",
                      "Test Automation Engineer", "Forward Deployed Engineer"]:
            with self.subTest(title=title):
                self.assertTrue(is_cs_role(title))

    def test_engineer_alone_is_not_a_cs_word(self):
        for title in ["Welding Engineer (Starship)", "Launch Operations Engineer", "Splunk Engineer",
                      "Material Flow Engineer", "Reliability Engineer", "Antenna Engineer (Starlink)",
                      "CNC Programmer (Starship Components)", "Telecommunications Engineer, Fiber",
                      "Antenna Engineer (Starlink Mobile)", "Supervisor, Quality Assurance (Starlink Aviation)"]:
            with self.subTest(title=title):
                self.assertFalse(is_cs_role(title))
        for title in ["Backend Engineer", "Founding Engineer", "Product Engineer", "AI Engineer",
                      "ML Engineer", "Data Engineer (Starlink)", "Network Security Engineer",
                      "Kubernetes Platform Infrastructure Engineer", "Platform Engineer, Flight Software",
                      "Operations Engineer, Applied AI (Application Software)"]:
            with self.subTest(title=title):
                self.assertTrue(is_cs_role(title))

    def test_clean_up_drops_experienced_roles(self):
        rows = clean_up([
            posting("Software Engineer", "Requirements: 5+ years of software experience"),
            posting("Software Engineer, Flight", "Bachelor's degree in computer science"),
        ], 1, NOW)
        self.assertEqual([row["title"] for row in rows], ["Software Engineer, Flight"])
        self.assertIn("Bachelor", rows[0]["description"])


if __name__ == "__main__":
    unittest.main()
