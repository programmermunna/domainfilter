import unittest

from domainfilter.parser import expand_domains, parse_names, parse_tlds


class TestParseNames(unittest.TestCase):
    def test_comma_separated_names(self):
        r = parse_names("Kormo, Srijon, Uddog")
        self.assertEqual(r.tokens, ["kormo", "srijon", "uddog"])
        self.assertEqual(r.skipped, [])

    def test_splits_on_newlines_spaces_semicolons(self):
        r = parse_names("kormo\nsrijon uddog;prava")
        self.assertEqual(r.tokens, ["kormo", "srijon", "uddog", "prava"])

    def test_dedupes_case_insensitively(self):
        r = parse_names("kormo, KORMO, kormo")
        self.assertEqual(r.tokens, ["kormo"])

    def test_skips_invalid_tokens(self):
        r = parse_names("bad_name!, srijon")
        self.assertEqual(r.tokens, ["srijon"])
        self.assertEqual(r.skipped, ["bad_name!"])

    def test_strips_url_pieces(self):
        r = parse_names("https://www.kormo.com/")
        self.assertEqual(r.tokens, ["kormo.com"])

    def test_empty_input(self):
        r = parse_names("   ")
        self.assertEqual(r.tokens, [])
        self.assertEqual(r.skipped, [])


class TestExpandDomains(unittest.TestCase):
    def test_expands_names_across_tlds(self):
        self.assertEqual(
            expand_domains(["kormo"], ["com", "ai"]),
            ["kormo.com", "kormo.ai"],
        )

    def test_exact_domain_not_reexpanded(self):
        self.assertEqual(expand_domains(["kormo.com"], ["com"]), ["kormo.com"])

    def test_mixed_tokens_deduped(self):
        self.assertEqual(
            expand_domains(["kormo", "kormo.com"], ["com", "ai"]),
            ["kormo.com", "kormo.ai"],
        )


class TestParseTlds(unittest.TestCase):
    def test_strips_dots_and_lowercases(self):
        self.assertEqual(parse_tlds("com, .AI, io"), ["com", "ai", "io"])

    def test_dedupes(self):
        self.assertEqual(parse_tlds("com, com, .com"), ["com"])


if __name__ == "__main__":
    unittest.main()
