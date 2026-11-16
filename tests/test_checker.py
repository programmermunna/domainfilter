import unittest

from domainfilter import checker
from domainfilter.checker import (
    BOOTSTRAP_URL,
    Status,
    check_domain,
    check_domains,
    iter_checked_domains,
    load_bootstrap,
    rdap_base_for,
)

BOOTSTRAP_JSON = (
    b'{"services": ['
    b'[["com", "net"], ["https://rdap.verisign.com/{tld}/v1/"]],'
    b'[["uk"], ["https://rdap.nominet.uk/uk/"]]'
    b']}'
)

BASE = "https://rdap.verisign.com/com/v1/"


def fake_fetch(url, timeout=10):
    if url == BOOTSTRAP_URL:
        return 200, BOOTSTRAP_JSON
    if url.endswith("domain/taken.com"):
        return 200, b"{}"
    if url.endswith("domain/free.com"):
        return 404, b"{}"
    return 500, b""


class FlakyFetcher:
    def __init__(self):
        self.calls = 0

    def __call__(self, url, timeout=10):
        self.calls += 1
        if self.calls == 1:
            return 429, b""
        return 200, b"{}"


class TestRdapBaseFor(unittest.TestCase):
    def setUp(self):
        self.bootstrap = load_bootstrap(fake_fetch)

    def test_resolves_from_bootstrap(self):
        self.assertEqual(
            rdap_base_for("com", self.bootstrap), "https://rdap.verisign.com/com/v1/"
        )

    def test_multi_label_tld_uses_registry_tld(self):
        self.assertEqual(
            rdap_base_for("co.uk", self.bootstrap), "https://rdap.nominet.uk/uk/"
        )

    def test_unknown_tld_returns_none(self):
        self.assertIsNone(rdap_base_for("notarealtld", self.bootstrap))


class TestCheckDomain(unittest.TestCase):
    def test_404_means_available(self):
        r = check_domain("free.com", BASE, fetch=fake_fetch)
        self.assertEqual(r.status, Status.AVAILABLE)
        self.assertEqual(r.domain, "free.com")

    def test_200_means_taken(self):
        r = check_domain("taken.com", BASE, fetch=fake_fetch)
        self.assertEqual(r.status, Status.TAKEN)

    def test_server_error_means_unknown(self):
        r = check_domain("weird.com", BASE, fetch=fake_fetch, retries=0)
        self.assertEqual(r.status, Status.UNKNOWN)

    def test_retries_on_429(self):
        r = check_domain("taken.com", BASE, fetch=FlakyFetcher(), retries=1)
        self.assertEqual(r.status, Status.TAKEN)


class TestCheckDomains(unittest.TestCase):
    def test_checks_many_and_preserves_order(self):
        results = check_domains(
            ["taken.com", "free.com"], fetch=fake_fetch, workers=2
        )
        self.assertEqual([r.domain for r in results], ["taken.com", "free.com"])
        self.assertEqual(results[0].status, Status.TAKEN)
        self.assertEqual(results[1].status, Status.AVAILABLE)

    def test_unsupported_tld_is_unknown(self):
        results = check_domains(["name.notarealtld"], fetch=fake_fetch, workers=1)
        self.assertEqual(results[0].status, Status.UNKNOWN)

    def test_result_carries_price(self):
        results = check_domains(["free.com"], fetch=fake_fetch, workers=1)
        self.assertIsNotNone(results[0].price)


class TestIterCheckedDomains(unittest.TestCase):
    def test_yields_results_in_order(self):
        it = iter_checked_domains(
            ["taken.com", "free.com"], fetch=fake_fetch, workers=2
        )
        self.assertFalse(isinstance(it, list))
        results = list(it)
        self.assertEqual([r.domain for r in results], ["taken.com", "free.com"])
        self.assertEqual(results[0].status, Status.TAKEN)
        self.assertEqual(results[1].status, Status.AVAILABLE)


if __name__ == "__main__":
    unittest.main()
