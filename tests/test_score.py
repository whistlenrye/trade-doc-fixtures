import json
import unittest
from pathlib import Path

from trade_doc_fixtures.__main__ import main
from trade_doc_fixtures.score import score_extraction

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def expected(name: str) -> dict:
    return json.loads((FIXTURES / name / "expected.json").read_text(encoding="utf-8"))


class ScoreTests(unittest.TestCase):
    def test_gold_matches_itself(self):
        for name in ("commercial_invoice", "packing_list", "bill_of_lading", "certificate_of_origin"):
            gold = expected(name)
            report = score_extraction(gold, gold)
            self.assertEqual(report["recall"], 1.0, name)
            self.assertEqual(report["misses"], [])
            text = (FIXTURES / name / "document.txt").read_text(encoding="utf-8")
            self.assertGreater(len(text), 80)

    def test_wrong_total_is_a_miss(self):
        gold = expected("commercial_invoice")
        actual = json.loads(json.dumps(gold))
        actual["total"] = 1
        report = score_extraction(actual, gold)
        self.assertLess(report["recall"], 1)
        self.assertIn("total", [item["path"] for item in report["misses"]])

    def test_missing_transport_is_scored_only_when_gold_has_it(self):
        gold = expected("bill_of_lading")
        actual = {key: value for key, value in gold.items() if key != "transport"}
        report = score_extraction(actual, gold)
        missed = {item["path"] for item in report["misses"]}
        self.assertIn("transport.ocean_bill", missed)
        self.assertNotIn("subtotal", missed)

    def test_catalog_lists_every_fixture(self):
        catalog = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
        names = {item["name"] for item in catalog["fixtures"]}
        self.assertEqual(
            names,
            {"commercial_invoice", "packing_list", "bill_of_lading", "certificate_of_origin"},
        )

    def test_cli_perfect_score(self):
        path = FIXTURES / "packing_list" / "expected.json"
        self.assertEqual(main([str(path), str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
