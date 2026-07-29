import json
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def canonical_url(value):
    parsed = urlsplit(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


class JournalDataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rank_config = json.loads(
            (REPO_ROOT / "_data" / "journal_rank.json").read_text(encoding="utf-8")
        )
        cls.jrank = yaml.safe_load(
            (REPO_ROOT / "_data" / "jrank.yml").read_text(encoding="utf-8")
        )
        cls.cfps = yaml.safe_load(
            (REPO_ROOT / "_data" / "cfps.yml").read_text(encoding="utf-8")
        )

    def test_rank_master_has_unique_names_source_ids_and_urls(self):
        for field in ("name", "sourceid", "url"):
            values = [item.get(field) for item in self.rank_config if item.get(field)]
            self.assertEqual(
                len(values),
                len(set(values)),
                f"journal_rank.json contains duplicate {field}",
            )

    def test_jrank_matches_master_exactly(self):
        master_names = {item["name"] for item in self.rank_config}
        output_names = [item["journal"] for item in self.jrank]
        self.assertEqual(len(output_names), len(set(output_names)), "jrank.yml contains duplicate journals")
        self.assertEqual(set(output_names), master_names, "jrank.yml and journal_rank.json have different journals")

    def test_cfps_have_valid_links_dates_and_unique_journal_links(self):
        seen = set()
        sort_keys = []
        for item in self.cfps:
            self.assertTrue(str(item.get("journal") or "").strip())
            self.assertTrue(str(item.get("title") or "").strip())
            link = canonical_url(item.get("link"))
            self.assertTrue(link, f"invalid CFP link: {item.get('journal')} / {item.get('title')}")
            key = (item["journal"], link)
            self.assertNotIn(key, seen, f"duplicate CFP URL for {item['journal']}: {link}")
            seen.add(key)

            sort_key = item.get("fullpaper_deadline_sort")
            sort_keys.append(sort_key or "9999-99-99")
            if sort_key != "9999-99-99":
                datetime.strptime(sort_key, "%Y-%m-%d")

        self.assertEqual(
            sort_keys,
            sorted(sort_keys),
            "cfps.yml is not ordered by its effective earliest deadline",
        )


if __name__ == "__main__":
    unittest.main()
