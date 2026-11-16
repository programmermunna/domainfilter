import unittest

from domainfilter.prices import format_price, price_for


class TestPriceFor(unittest.TestCase):
    def test_known_tld_returns_float(self):
        price = price_for("com")
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0)

    def test_accepts_leading_dot_and_uppercase(self):
        self.assertEqual(price_for(".COM"), price_for("com"))

    def test_unknown_tld_returns_none(self):
        self.assertIsNone(price_for("notarealtld"))


class TestFormatPrice(unittest.TestCase):
    def test_formats_usd_per_year(self):
        self.assertEqual(format_price(11.99), "$11.99/yr")

    def test_none_renders_dash(self):
        self.assertEqual(format_price(None), "-")


if __name__ == "__main__":
    unittest.main()
