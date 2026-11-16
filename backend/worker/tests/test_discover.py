import sys
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import discover
import pipeline

NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)


def row(title="Software Engineer Intern", location="New York, NY"):
    return {"title": title, "location": location, "company_id": 0,
            "dedupe_hash": pipeline.make_fingerprint(0, title, location)}


class JobSystemTests(unittest.TestCase):
    def test_reads_board_names_from_links(self):
        cases = {
            "https://job-boards.greenhouse.io/stripe/jobs/123": ("greenhouse", "stripe"),
            "https://boards.greenhouse.io/embed/job_app?for=Figma&token=1": ("greenhouse", "figma"),
            "https://jobs.lever.co/Palantir/abc-123/apply": ("lever", "palantir"),
            "https://jobs.ashbyhq.com/ramp/9f2e?utm_source=Simplify": ("ashby", "ramp"),
        }
        for url, expected in cases.items():
            self.assertEqual(discover.job_system(url), expected, url)

    def test_other_systems_have_no_board(self):
        self.assertEqual(discover.job_system("https://acme.wd5.myworkdayjobs.com/x/job/1"), ("Workday", None))
        self.assertEqual(discover.job_system("https://www.metacareers.com/jobs/1"), ("Company's own site", None))
        self.assertEqual(discover.job_system(""), ("Company's own site", None))

    def test_board_takes_the_most_common_company_name(self):
        postings = [
            {"company_name": "Ramp", "url": "https://jobs.ashbyhq.com/ramp/1"},
            {"company_name": "Ramp", "url": "https://jobs.ashbyhq.com/ramp/2"},
            {"company_name": "Ramp Inc", "url": "https://jobs.ashbyhq.com/ramp/3"},
            {"company_name": "Meta", "url": "https://www.metacareers.com/jobs/1"},
        ]
        self.assertEqual(discover.find_boards(postings), {("ashby", "ramp"): "Ramp"})


class PlanTests(unittest.TestCase):
    def test_adds_only_new_working_boards_with_jobs(self):
        results = [
            ("ashby", "ramp", True, 50, [row(), row("Data Analyst Intern")]),
            ("lever", "dead", False, 0, []),
            ("lever", "empty", True, 10, []),
            ("greenhouse", "stripe", True, 99, [row()]),          # already collected
            ("greenhouse", "stripe-eu", True, 5, [row()]),        # name already used
        ]
        names = {("ashby", "ramp"): "Ramp", ("lever", "dead"): "Dead Co", ("lever", "empty"): "Empty Co",
                 ("greenhouse", "stripe"): "Stripe", ("greenhouse", "stripe-eu"): "Stripe"}
        existing = [{"name": "Stripe", "ats_type": "greenhouse", "ats_slug": "stripe"}]
        to_add, skipped = discover.plan_additions(results, names, existing, min_jobs=1)
        self.assertEqual([(n, s, b) for n, s, b, _ in to_add], [("Ramp", "ashby", "ramp")])
        self.assertEqual(sorted(name for name, _ in skipped), ["Dead Co", "Empty Co", "Stripe"])

    def test_rows_are_rekeyed_for_the_real_company(self):
        rekeyed = discover.with_company_id([row()], 42)
        self.assertEqual(rekeyed[0]["company_id"], 42)
        self.assertEqual(rekeyed[0]["dedupe_hash"], pipeline.make_fingerprint(42, "Software Engineer Intern", "New York, NY"))


class AddCompaniesTests(unittest.TestCase):
    def test_inserts_company_then_saves_jobs_without_alerts(self):
        calls = []

        class Query:
            def insert(self, values):
                calls.append(("insert", values))
                return self

            def execute(self):
                return SimpleNamespace(data=[{"id": 7}])

        client = SimpleNamespace(table=lambda name: Query())
        with mock.patch.object(pipeline, "save", side_effect=lambda c, rows, cid: calls.append(("save", cid, rows))) as save, \
             mock.patch.object(pipeline, "notify_new_jobs") as notify:
            added, jobs = discover.add_companies(client, [("Ramp", "ashby", "ramp", [row()])])
        self.assertEqual((added, jobs), (1, 1))
        self.assertEqual(calls[0], ("insert", {"name": "Ramp", "ats_type": "ashby", "ats_slug": "ramp"}))
        self.assertEqual(calls[1][1], 7)
        self.assertEqual(calls[1][2][0]["company_id"], 7)
        save.assert_called_once()
        notify.assert_not_called()

    def test_one_failed_insert_does_not_stop_the_rest(self):
        class Query:
            def __init__(self):
                self.values = None

            def insert(self, values):
                self.values = values
                return self

            def execute(self):
                if self.values["name"] == "Broken":
                    raise RuntimeError("duplicate key")
                return SimpleNamespace(data=[{"id": 8}])

        client = SimpleNamespace(table=lambda name: Query())
        with mock.patch.object(pipeline, "save"):
            added, _ = discover.add_companies(client, [("Broken", "lever", "b", [row()]), ("Ramp", "ashby", "ramp", [row()])])
        self.assertEqual(added, 1)


class PipelineDownloadTests(unittest.TestCase):
    def test_download_all_keeps_order_and_reports_failures(self):
        companies = [{"id": i, "name": f"C{i}", "ats_type": "greenhouse", "ats_slug": f"c{i}"} for i in range(70)]

        def fake_collect(ats_type, slug):
            if slug == "c5":
                raise ValueError("board gone")
            return [{"title": "Software Engineer Intern", "absolute_url": f"https://x/{slug}",
                     "location": {"name": "Austin, TX"}}]

        with mock.patch.object(pipeline, "collect", side_effect=fake_collect):
            results = list(pipeline.download_all(companies, NOW))
        self.assertEqual([r[0]["id"] for r in results], list(range(70)))
        self.assertIsInstance(results[5][3], ValueError)
        self.assertEqual(len(results[6][2]), 1)
        self.assertEqual(results[6][2][0]["company_id"], 6)


if __name__ == "__main__":
    unittest.main()
