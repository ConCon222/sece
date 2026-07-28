import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(module_name, relative_path):
    spec = importlib.util.spec_from_file_location(module_name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scopus = load_script("test_update_scopus_metrics", "bin/update_scopus_metrics.py")
manager_module = load_script("test_journal_data_manager", "bin/journal_data_manager.py")
ranking = load_script("test_journal_ranking_updater", "bin/journal_ranking_updater.py")


class ScopusMetricMergeTests(unittest.TestCase):
    def test_missing_document_metrics_preserve_existing_values(self):
        journal = {
            "documents_current_year": "51 (2026)",
            "documents_last_year": "120 (2025)",
            "documents_published": "120 (2025)",
        }
        old_values = journal.copy()

        changed = scopus._merge_scopus_metrics(
            journal,
            {
                "orange_score": None,
                "orange_quartile": None,
                "orange_percentile": None,
                "docs_current_year": None,
                "docs_last_year": None,
            },
        )

        self.assertFalse(changed)
        self.assertEqual(journal, old_values)

    def test_parsed_document_metrics_update_compatibility_field(self):
        journal = {
            "documents_current_year": "51 (2026)",
            "documents_last_year": "120 (2025)",
            "documents_published": "120 (2025)",
        }

        changed = scopus._merge_scopus_metrics(
            journal,
            {
                "docs_current_year": "60 (2026)",
                "docs_last_year": "130 (2025)",
            },
        )

        self.assertTrue(changed)
        self.assertEqual(journal["documents_current_year"], "60 (2026)")
        self.assertEqual(journal["documents_last_year"], "130 (2025)")
        self.assertEqual(journal["documents_published"], "130 (2025)")

    def test_future_volume_does_not_shift_current_and_previous_year(self):
        current, previous = scopus._select_document_years(
            [(2027, "11"), (2026, "596"), (2025, "481")],
            current_year=2026,
        )
        self.assertEqual(current, "596")
        self.assertEqual(previous, "481")


class JournalManagerStateTests(unittest.TestCase):
    def _manager_in(self, directory, journal_count=4):
        root = Path(directory)
        config_file = root / "journal_rank.json"
        config_file.write_text(
            json.dumps([{"name": f"Journal {index}"} for index in range(journal_count)]),
            encoding="utf-8",
        )
        jrank_file = root / "jrank.yml"
        jrank_file.write_text("[]\n", encoding="utf-8")

        manager = manager_module.JournalDataManager()
        manager.journal_rank_file = str(config_file)
        manager.jrank_file = str(jrank_file)
        manager.cursor_file = str(root / ".rank_cursor")
        manager.meta_file = str(root / "jrank_meta.yml")
        return manager

    def test_failed_child_does_not_advance_cursor_or_write_success_meta(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager_in(directory)
            Path(manager.cursor_file).write_text("1", encoding="utf-8")
            manager.run_scopus_update = mock.Mock(return_value=False)
            manager.run_publisher_update = mock.Mock(return_value=True)

            success = manager.run_all(show_diff=False, batch_size=2)

            self.assertFalse(success)
            self.assertEqual(Path(manager.cursor_file).read_text(encoding="utf-8"), "1")
            self.assertFalse(Path(manager.meta_file).exists())

    def test_child_process_inherits_live_output_streams(self):
        manager = manager_module.JournalDataManager()
        completed = mock.Mock(returncode=0)
        with mock.patch.object(manager_module.os.path, "exists", return_value=True):
            with mock.patch.object(manager_module.subprocess, "run", return_value=completed) as run:
                success = manager.run_scopus_update()

        self.assertTrue(success)
        command = run.call_args.args[0]
        self.assertIn("-u", command)
        self.assertNotIn("capture_output", run.call_args.kwargs)

    def test_successful_children_advance_cursor_and_write_meta(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager_in(directory)
            Path(manager.cursor_file).write_text("1", encoding="utf-8")
            manager.run_scopus_update = mock.Mock(return_value=True)
            manager.run_publisher_update = mock.Mock(return_value=True)

            success = manager.run_all(show_diff=False, batch_size=2)

            self.assertTrue(success)
            self.assertEqual(Path(manager.cursor_file).read_text(encoding="utf-8"), "3")
            metadata = yaml.safe_load(Path(manager.meta_file).read_text(encoding="utf-8"))
            self.assertEqual(metadata["batch_offset"], 1)
            self.assertEqual(metadata["batch_size"], 2)
            self.assertEqual(metadata["journal_count"], 4)
            self.assertRegex(metadata["last_successful_update"], r"^\d{4}-\d{2}-\d{2}$")


class FlareSolverrValidationTests(unittest.TestCase):
    def test_rejects_error_status_and_challenge_documents(self):
        self.assertTrue(ranking.FlareSolverrClient.is_error_page("<html>ok</html>", 503))
        self.assertTrue(
            ranking.FlareSolverrClient.is_error_page(
                "<html><title>Just a moment...</title><div class='cf-chl-widget'></div></html>",
                200,
            )
        )
        self.assertFalse(
            ranking.FlareSolverrClient.is_error_page(
                "<html><title>Journal metrics</title><p>Acceptance rate 9%</p></html>",
                200,
            )
        )
        self.assertFalse(
            ranking.FlareSolverrClient.is_error_page(
                "<html><title>Journal metrics</title><p>Acceptance rate 9%</p>"
                "<script src='/challenge-platform/script.js'></script></html>",
                200,
            )
        )

    def test_empty_configuration_is_a_failure(self):
        updater = object.__new__(ranking.JournalRankingUpdater)
        updater.load_journal_data = lambda: ([], [])

        self.assertFalse(updater.update_journal_rankings())


class PublisherTargetFixtureTests(unittest.TestCase):
    class FakeClient:
        def __init__(self, html):
            self.html = html

        def get_page(self, _url):
            return self.html

    def test_wiley_current_metrics_markup(self):
        html = """
        <h4><span>Acceptance rate:</span></h4><p>9%</p>
        <h4><span>Submission to first decision (median):</span></h4><p>32 days</p>
        <h4><span>Submission to acceptance (median):</span></h4><p>267 days</p>
        <h4><span>Acceptance to publication (median):</span></h4><p>19 days</p>
        """
        metrics = ranking.WileyCrawler(self.FakeClient(html)).extract_metrics(
            "https://onlinelibrary.wiley.com/journal/13652729/journal-metrics"
        )
        self.assertEqual(metrics["acceptance_rate"], "9%")
        self.assertEqual(metrics["first_decision_time"], "32 days")
        self.assertEqual(metrics["acceptance_time"], "267 days")
        self.assertEqual(metrics["publication_time"], "19 days")

    def test_taylor_francis_current_metrics_markup(self):
        html = """
        <ul>
          <li><strong>25</strong> days avg. from submission to first decision</li>
          <li><strong>63</strong> days avg. from submission to first post-review decision</li>
          <li><strong>6</strong>% acceptance rate</li>
        </ul>
        """
        metrics = ranking.TaylorFrancisCrawler(self.FakeClient(html)).extract_metrics(
            "https://www.tandfonline.com/journals/hedp20/about-this-journal"
        )
        self.assertEqual(metrics["first_decision_time"], "25 days")
        self.assertEqual(metrics["review_time"], "63 days")
        self.assertEqual(metrics["acceptance_rate"], "6%")

    def test_springer_current_metrics_markup(self):
        html = '<dd data-test="metrics-speed-value"><span>22 days</span></dd>'
        metrics = ranking.SpringerCrawler(self.FakeClient(html)).extract_metrics(
            "https://link.springer.com/journal/11423"
        )
        self.assertEqual(metrics["first_decision_time"], "22 days")

    def test_nature_current_impact_markup(self):
        response = mock.Mock(
            status_code=200,
            text=(
                "<li>Submission to first editorial decision (median days): 15</li>"
                "<li>Submission to acceptance (median days): 187</li>"
            ),
        )
        with mock.patch.object(ranking.requests, "get", return_value=response):
            metrics = ranking.NatureCrawler().extract_metrics(
                "https://www.nature.com/npjscilearn"
            )
        self.assertEqual(metrics["first_decision_time"], "15 days")
        self.assertEqual(metrics["acceptance_time"], "187 days")

    def test_nature_summary_fallback_for_redirected_journal(self):
        about_response = mock.Mock(status_code=200, text="<html><title>About</title></html>")
        summary_response = mock.Mock(
            status_code=200,
            text="""
            <table><tr>
              <td><a href="https://www.nature.com/srep/">Scientific Reports</a></td>
              <td><p>12</p></td><td><p>138</p></td>
            </tr></table>
            """,
        )
        with mock.patch.object(
            ranking.requests,
            "get",
            side_effect=[about_response, summary_response],
        ):
            metrics = ranking.NatureCrawler().extract_metrics(
                "https://www.nature.com/srep"
            )
        self.assertEqual(metrics["first_decision_time"], "12 days")
        self.assertEqual(metrics["acceptance_time"], "138 days")

    def test_uchicago_revise_share_is_not_acceptance_rate(self):
        html = (
            "Desk Rejection 39% 1 2 "
            "Reject with Reviews 53% 20 70 "
            "Revise 9% 80 120"
        )
        client = self.FakeClient(html)
        client.destroy_session = lambda: None
        metrics = ranking.UChicagoCrawler(client).extract_metrics(
            "https://www.journals.uchicago.edu/journals/jpe"
        )
        self.assertNotIn("acceptance_rate", metrics)


class PublisherPipelineReliabilityTests(unittest.TestCase):
    def _updater(self, journal_list, existing_data, crawler_result=None):
        updater = object.__new__(ranking.JournalRankingUpdater)
        updater.load_journal_data = lambda: (journal_list, existing_data)
        updater.get_publisher_from_url = lambda _url: "wiley"
        updater.publisher_crawlers = {
            "wiley": mock.Mock(
                extract_metrics=mock.Mock(return_value=crawler_result or {})
            )
        }
        updater.publisher_display_names = {"wiley": "Wiley"}
        updater.infer_publisher_display = lambda _url: None
        updater.easyscholar_crawler = None
        updater.calculate_hm_score = lambda _item: 0
        updater.flaresolverr_client = mock.Mock()
        return updater

    def test_all_publisher_requests_failing_is_not_success(self):
        updater = self._updater(
            [{"name": "Test Journal", "url": "https://onlinelibrary.wiley.com/journal/test"}],
            [{"journal": "Test Journal", "publisher": "Wiley", "tag": []}],
        )
        with mock.patch.object(ranking.time, "sleep"):
            success = updater.update_journal_rankings(dry_run=True)
        self.assertFalse(success)

    def test_removed_master_entries_are_pruned_on_save(self):
        updater = self._updater(
            [{"name": "Kept Journal", "url": ""}],
            [
                {"journal": "Kept Journal", "publisher": "", "tag": []},
                {"journal": "Removed Journal", "publisher": "", "tag": []},
            ],
        )
        updater.get_publisher_from_url = lambda _url: None
        updater.publisher_crawlers = {}
        captured = []

        def capture(data, _path):
            captured.extend(data)
            return True

        with mock.patch.object(ranking, "_atomic_write_yaml", side_effect=capture), mock.patch.object(
            ranking.time,
            "sleep",
        ):
            success = updater.update_journal_rankings()
        self.assertTrue(success)
        self.assertEqual([item["journal"] for item in captured], ["Kept Journal"])


if __name__ == "__main__":
    unittest.main()
