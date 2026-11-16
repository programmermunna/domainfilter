import json
import tempfile
import unittest
from pathlib import Path

from domainfilter.checker import Result, Status
from domainfilter.report import write_reports


def sample_results():
    return [
        Result("kormo.com", Status.TAKEN, "com", 11.99),
        Result("kormo.io", Status.AVAILABLE, "io", 39.99),
        Result("srijon.xyz", Status.AVAILABLE, "xyz", 2.99),
        Result("uddog.badtl", Status.UNKNOWN, "badtl", None),
    ]


class TestWriteReports(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp.name)
        self.paths = write_reports(sample_results(), self.out_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_available_file_has_only_available_domains_with_prices(self):
        text = (self.out_dir / "available.txt").read_text()
        self.assertIn("kormo.io", text)
        self.assertIn("$39.99", text)
        self.assertIn("srijon.xyz", text)
        self.assertNotIn("kormo.com", text)

    def test_taken_file(self):
        text = (self.out_dir / "taken.txt").read_text()
        self.assertIn("kormo.com", text)
        self.assertNotIn("kormo.io", text)

    def test_unknown_file(self):
        text = (self.out_dir / "unknown.txt").read_text()
        self.assertIn("uddog.badtl", text)

    def test_report_json_contains_everything(self):
        data = json.loads((self.out_dir / "report.json").read_text())
        self.assertEqual(len(data), 4)
        by_domain = {d["domain"]: d for d in data}
        self.assertEqual(by_domain["kormo.io"]["status"], "available")
        self.assertEqual(by_domain["kormo.com"]["status"], "taken")

    def test_report_csv_exists(self):
        text = (self.out_dir / "report.csv").read_text()
        self.assertIn("domain,status,price_usd_year", text.splitlines()[0])

    def test_returns_paths(self):
        self.assertIn("available", self.paths)
        self.assertIn("report_json", self.paths)

    def test_unknown_file_absent_when_none_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            results = [r for r in sample_results() if r.status != Status.UNKNOWN]
            write_reports(results, Path(d))
            self.assertFalse((Path(d) / "unknown.txt").exists())

    def test_stem_creates_named_directory(self):
        with tempfile.TemporaryDirectory() as d:
            paths = write_reports(sample_results(), Path(d), stem="names")
            self.assertTrue((Path(d) / "names" / "available.txt").exists())
            self.assertTrue((Path(d) / "names" / "taken.txt").exists())
            self.assertTrue((Path(d) / "names" / "report.json").exists())
            self.assertIn("kormo.io", (Path(d) / "names" / "available.txt").read_text())

    def test_rerun_same_stem_clears_stale_files(self):
        with tempfile.TemporaryDirectory() as d:
            write_reports(sample_results(), Path(d), stem="names")
            self.assertTrue((Path(d) / "names" / "unknown.txt").exists())
            clean = [r for r in sample_results() if r.status != Status.UNKNOWN]
            write_reports(clean, Path(d), stem="names")
            self.assertFalse((Path(d) / "names" / "unknown.txt").exists())
            self.assertNotIn("uddog.badtl", (Path(d) / "names" / "taken.txt").read_text())


if __name__ == "__main__":
    unittest.main()
