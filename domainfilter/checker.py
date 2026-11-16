"""Domain availability checking via RDAP (free, no API key needed).

RDAP is the official successor to WHOIS. The IANA bootstrap registry maps
each TLD to its registry's RDAP server; a 404 response means the domain is
not registered (available), a 200 means it exists (taken).
"""

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from . import __version__
from .prices import price_for

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
USER_AGENT = f"domainfilter/{__version__} (+https://github.com/programmermunna/domainfilter)"

# Fallback RDAP endpoints used if the IANA bootstrap file can't be fetched.
FALLBACK_RDAP = {
    "com": "https://rdap.verisign.com/com/v1/",
    "net": "https://rdap.verisign.com/net/v1/",
    "org": "https://rdap.publicinterestregistry.org/rdap/",
    "info": "https://rdap.identitydigital.services/rdap/",
    "biz": "https://rdap.identitydigital.services/rdap/",
    "io": "https://rdap.identitydigital.services/rdap/",
    "dev": "https://rdap.nic.google/",
    "app": "https://rdap.nic.google/",
    "co": "https://rdap.nic.co/",
    "me": "https://rdap.nic.me/",
    "us": "https://rdap.nic.us/",
    "uk": "https://rdap.nominet.uk/uk/",
    "ca": "https://rdap.ca.fury.ca/rdap/",
    "de": "https://rdap.denic.de/",
    "in": "https://rdap.registry.in/rdap/",
    "xyz": "https://rdap.centralnic.com/xyz/",
    "tv": "https://rdap.nic.tv/",
    "cc": "https://rdap.nic.cc/",
}


class Status(Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    UNKNOWN = "unknown"


@dataclass
class Result:
    domain: str
    status: Status
    tld: str
    price: float  # estimated first-year USD, or None


def default_fetch(url, timeout=10):
    """HTTP GET -> (status_code, body). Returns (-1, b'') on network errors."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rdap+json, application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, body
    except Exception:
        return -1, b""


def load_bootstrap(fetch=default_fetch, timeout=10):
    """TLD -> RDAP base URL map, from IANA bootstrap with bundled fallback."""
    mapping = dict(FALLBACK_RDAP)
    status, body = fetch(BOOTSTRAP_URL, timeout)
    if status == 200:
        try:
            data = json.loads(body.decode("utf-8", "replace"))
            for tlds, urls in data.get("services", []):
                if not urls:
                    continue
                for tld in tlds:
                    mapping[tld.lower()] = urls[0].replace("{tld}", tld.lower())
        except (ValueError, AttributeError):
            pass
    return mapping


def rdap_base_for(tld, bootstrap):
    """RDAP base URL for a TLD ('co.uk' resolves via its 'uk' registry)."""
    key = tld.lower().lstrip(".")
    if key in bootstrap:
        return bootstrap[key]
    return bootstrap.get(key.split(".")[-1])


def tld_of(domain):
    return domain.split(".", 1)[1]


def check_domain(domain, base, fetch=default_fetch, timeout=10, retries=2):
    """Check one domain against an RDAP base URL."""
    tld = tld_of(domain)
    url = f"{base.rstrip('/')}/domain/{domain}"
    for attempt in range(retries + 1):
        status, _ = fetch(url, timeout)
        if status == 404:
            result_status = Status.AVAILABLE
            break
        if status == 200:
            result_status = Status.TAKEN
            break
        if status == -1 or status == 429 or status >= 500:
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue
        return Result(domain, Status.UNKNOWN, tld, price_for(tld))
    return Result(domain, result_status, tld, price_for(tld))


def iter_checked_domains(domains, fetch=default_fetch, workers=8, timeout=10, retries=2):
    """Check domains in parallel, yielding each Result in input order as it
    completes — callers can print progress while the run is still going."""
    bootstrap = load_bootstrap(fetch, timeout)

    def _check(domain):
        base = rdap_base_for(tld_of(domain), bootstrap)
        if base is None:
            return Result(domain, Status.UNKNOWN, tld_of(domain), price_for(tld_of(domain)))
        return check_domain(domain, base, fetch=fetch, timeout=timeout, retries=retries)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        yield from pool.map(_check, domains)


def check_domains(domains, fetch=default_fetch, workers=8, timeout=10, retries=2):
    """Check many domains in parallel. Preserves input order."""
    return list(
        iter_checked_domains(
            domains, fetch=fetch, workers=workers, timeout=timeout, retries=retries
        )
    )
