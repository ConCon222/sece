import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "scrape_cfps.py"
SPEC = importlib.util.spec_from_file_location("scrape_cfps", MODULE_PATH)
scrape_cfps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scrape_cfps)


class CFPParserTests(unittest.TestCase):
    def setUp(self):
        self.scraper = scrape_cfps.JournalCFPScraper()

    def test_date_ranges_months_and_invalid_dates(self):
        self.assertEqual(
            self.scraper.parse_date_to_sort_key("13 Jun 2025 to 30 Sep 2025"),
            "2025-09-30",
        )
        self.assertEqual(self.scraper.parse_date_to_sort_key("March 2027"), "2027-03-31")
        self.assertEqual(
            self.scraper.parse_date_to_sort_key("31 February 2027"),
            "9999-99-99",
        )

    def test_wiley_combined_abstract_and_full_paper_deadlines(self):
        html = """
        <html><body>
          <h4><a href="/journal/call-for-papers/inclusive-ai">Building Inclusive AI</a></h4>
          <p>
            <strong>Deadline for abstract submissions: 2 February 2027</strong><br>
            <strong>Deadline for full paper submissions: 31 August 2027</strong>
          </p>
          <h4><a href="/doi/10.1111/example">Ordinary published article</a></h4>
          <p>Published research article</p>
        </body></html>
        """
        results = self.scraper.parse_wiley_from_html(html, "https://example.wiley.com/journal")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["abstract_deadline"], "2 February 2027")
        self.assertEqual(results[0]["fullpaper_deadline"], "31 August 2027")

    def test_taylor_francis_rejects_guidance_page(self):
        guidance = """
        <html><body><h2>Tools, tips, and journal insights</h2>
        <p>Advice for early career reviewers.</p></body></html>
        """
        self.assertIsNone(
            self.scraper._tf_parse_detail_page_html(
                guidance,
                "https://think.taylorandfrancis.com/early-career-reviewer/",
            )
        )

        cfp = """
        <html><body>
          <section class="layout__hero"><h2>AI and Learning</h2></section>
          <section class="layout__deadline--title">
            <h3>Manuscript deadline</h3><time>30 September 2027</time>
          </section>
        </body></html>
        """
        result = self.scraper._tf_parse_detail_page_html(
            cfp,
            "https://think.taylorandfrancis.com/special_issues/ai-learning/",
        )
        self.assertEqual(result["fullpaper_deadline"], "30 September 2027")

    def test_generic_parser_finds_ets_announcement(self):
        html = """
        <html><body><main>
          <article>
            <h3><a href="https://drive.google.com/example">
              Call for papers for a special issue on Sustainable Educational Data
            </a></h3>
            <p>Abstract submission deadline: 31 August 2027.</p>
          </article>
        </main></body></html>
        """
        results = self.scraper.parse_generic_cfp_page(html, "https://www.j-ets.net/")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["abstract_deadline"], "31 August 2027")

    def test_pnas_publication_date_is_not_a_deadline(self):
        html = """
        <div class="card--row-reversed">
          <h3 class="card__title"><a href="/call/example">A real call for papers</a></h3>
          <span class="card__meta__date">July 20, 2026</span>
          <div>Submit work to this special issue.</div>
        </div>
        """
        results = self.scraper.parse_pnas(html, "https://www.pnas.org/author-center/")
        self.assertEqual(results[0]["fullpaper_deadline"], "未找到日期")

    def test_nature_scans_all_pages_and_marks_complete(self):
        page_one = """
        <html><body>
          <a class="c-pagination__link" href="?filter=Open&page=2">2</a>
          <article><div data-test="open-status">Open for submissions</div>
            <h3 itemprop="name headline"><a href="/collections/one">One</a></h3>
          </article>
        </body></html>
        """
        page_two = """
        <html><body>
          <article><div data-test="open-status">Open for submissions</div>
            <h3 itemprop="name headline"><a href="/collections/two">Two</a></h3>
          </article>
        </body></html>
        """
        with patch.object(self.scraper, "_fetch_nature_html", return_value=page_two), patch.object(
            self.scraper,
            "_fetch_nature_deadline",
            return_value="31 December 2027",
        ):
            results = self.scraper.parse_nature_collections(
                page_one,
                "https://www.nature.com/ncomms/collections?filter=Open",
            )
        self.assertEqual({item["title"] for item in results}, {"One", "Two"})
        self.assertTrue(self.scraper._nature_scan_complete)

    def test_oup_explicit_detail_page(self):
        html = """
        <html><body><main>
          <h1>Special Issue Call for Papers 2027</h1>
          <h3>Who Are We Studying in Communication Research?</h3>
          <p>Abstract submission deadline: 31 August 2027.</p>
          <table><tr><td>March 2028</td><td>Full Paper Submission Deadline</td></tr></table>
        </main></body></html>
        """
        results = self.scraper.parse_oup(
            html,
            "https://academic.oup.com/hcr/pages/special-issue-call-for-papers-2027",
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Who Are We Studying in Communication Research?")
        self.assertEqual(results[0]["abstract_deadline"], "31 August 2027")
        self.assertEqual(results[0]["fullpaper_deadline"], "March 2028")

    def test_merge_replaces_verified_journal_and_removes_junk(self):
        existing = [
            {
                "journal": "Nature Test",
                "publisher": "Nature Portfolio",
                "tag": [],
                "title": "Old open collection",
                "abstract_deadline": "",
                "fullpaper_deadline": "",
                "fullpaper_deadline_sort": "9999-99-99",
                "editors": "",
                "link": "https://www.nature.com/collections/old",
                "description": "",
            },
            {
                "journal": "AERA Open",
                "publisher": "SAGE",
                "tag": [],
                "title": "Learn about our Special Collections",
                "abstract_deadline": "",
                "fullpaper_deadline": "",
                "fullpaper_deadline_sort": "9999-99-99",
                "editors": "",
                "link": "",
                "description": "",
            },
        ]
        replacement = dict(existing[0])
        replacement.update(
            title="New open collection",
            link="https://www.nature.com/collections/new",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "cfps.yml"
            output.write_text(yaml.safe_dump(existing), encoding="utf-8")
            merged = self.scraper.merge_and_clean_records(
                [replacement],
                str(output),
                replace_journals={"Nature Test"},
            )
        self.assertEqual([item["title"] for item in merged], ["New open collection"])


if __name__ == "__main__":
    unittest.main()
