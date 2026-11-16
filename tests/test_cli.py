import json
import tempfile
import unittest
from pathlib import Path

from domainfilter.checker import BOOTSTRAP_URL
from domainfilter.cli import main

BOOTSTRAP_JSON = (
    b'{"services": [['
    b'["com", "net"], ["https://rdap.test/{tld}/v1/"]'
    b"]]}".replace(b" ", b"")
)


def fake_fetch(url, timeout=10):
    if url == BOOTSTRAP_URL:
        return 200, BOOTSTRAP_JSON
    if url.endswith("domain/kormo.com"):
        return 404, b"{}"
    if url.endswith("domain/google.com"):
        return 200, b"{}"
    return 404, b"{}"


class TestCliEndToEnd(unittest.TestCase):
    def test_comma_input_writes_filtered_files(self):
        with tempfile.TemporaryDirectory() as d:
            code = main(
                ["kormo, google", "--tlds", "com", "-o", d, "--no-color"],
                fetch=fake_fetch,
            )
            self.assertEqual(code, 0)
            available = (Path(d) / "available.txt").read_text()
            taken = (Path(d) / "taken.txt").read_text()
            self.assertIn("kormo.com", available)
            self.assertIn("google.com", taken)

    def test_input_file(self):
        with tempfile.TemporaryDirectory() as d:
            names = Path(d) / "names.txt"
            names.write_text("kormo, srijon\n")
            out = Path(d) / "out"
            code = main(
                ["-i", str(names), "--tlds", "com", "-o", str(out)],
                fetch=fake_fetch,
            )
            self.assertEqual(code, 0)
            self.assertIn("srijon.com", (out / "names" / "available.txt").read_text())

    def test_input_multiple_files(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("kormo\n")
            b.write_text("google\n")
            out = Path(d) / "out"
            code = main(
                ["-i", str(a), str(b), "--tlds", "com", "-o", str(out)],
                fetch=fake_fetch,
            )
            self.assertEqual(code, 0)
            combined = out / "combined"
            self.assertIn("kormo.com", (combined / "available.txt").read_text())
            self.assertIn("google.com", (combined / "taken.txt").read_text())

    def test_input_folder_reads_txt_files(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / "inputs"
            inp.mkdir()
            (inp / "a.txt").write_text("kormo\n")
            (inp / "b.txt").write_text("google\n")
            (inp / "notes.md").write_text("shouldbeignored\n")
            out = Path(d) / "out"
            code = main(
                ["-i", str(inp), "--tlds", "com", "-o", str(out)],
                fetch=fake_fetch,
            )
            self.assertEqual(code, 0)
            results = json.loads((out / "inputs" / "report.json").read_text())
            self.assertEqual(len(results), 2)

    def test_input_glob_pattern(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.txt").write_text("kormo\n")
            (Path(d) / "b.txt").write_text("srijon\n")
            out = Path(d) / "out"
            code = main(
                ["-i", str(Path(d) / "*.txt"), "--tlds", "com", "-o", str(out)],
                fetch=fake_fetch,
            )
            self.assertEqual(code, 0)
            results = json.loads((out / "combined" / "report.json").read_text())
            self.assertEqual(len(results), 2)

    def test_json_output_file_has_statuses(self):
        with tempfile.TemporaryDirectory() as d:
            main(["kormo", "--tlds", "com", "-o", d], fetch=fake_fetch)
            data = json.loads((Path(d) / "report.json").read_text())
            self.assertEqual(data[0]["domain"], "kormo.com")
            self.assertEqual(data[0]["status"], "available")


if __name__ == "__main__":
    unittest.main()
