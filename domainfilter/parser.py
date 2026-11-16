"""Parse comma-separated names/TLDs into clean domain tokens."""

import re
from dataclasses import dataclass, field

# A DNS label: letters, digits, hyphens; no leading/trailing hyphen; 1-63 chars.
LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
# A full domain: one or more labels separated by dots, ending in an alpha TLD.
DOMAIN_RE = re.compile(
    r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$"
)

_SPLIT_RE = re.compile(r"[,;\s]+")
_URL_STRIP_RE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass
class ParseResult:
    tokens: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _clean_token(token):
    token = _URL_STRIP_RE.sub("", token.strip())
    token = token.strip("/").strip().lower()
    if token.startswith("www."):
        token = token[4:]
    return token


def _is_valid_token(token):
    if "." in token:
        return bool(DOMAIN_RE.match(token))
    return bool(LABEL_RE.match(token))


def parse_names(text):
    """Split comma/space/newline-separated input into cleaned, deduped tokens.

    Tokens containing a dot are treated as exact domains; everything else as
    bare names to expand across the chosen TLDs.
    """
    result = ParseResult()
    seen = set()
    for raw in _SPLIT_RE.split(text):
        token = _clean_token(raw)
        if not token:
            continue
        if not _is_valid_token(token):
            result.skipped.append(token)
            continue
        if token in seen:
            continue
        seen.add(token)
        result.tokens.append(token)
    return result


def expand_domains(tokens, tlds):
    """Expand bare names across tlds; dotted tokens are checked as-is."""
    domains = []
    seen = set()
    for token in tokens:
        candidates = [token] if "." in token else [f"{token}.{t}" for t in tlds]
        for domain in candidates:
            if domain not in seen:
                seen.add(domain)
                domains.append(domain)
    return domains


def parse_tlds(text):
    """Parse a comma-separated TLD list: 'com, .AI, io' -> ['com', 'ai', 'io']."""
    tlds = []
    seen = set()
    for raw in _SPLIT_RE.split(text):
        tld = raw.strip().lstrip(".").lower()
        if not tld or tld in seen:
            continue
        seen.add(tld)
        tlds.append(tld)
    return tlds
