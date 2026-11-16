"""Estimated first-year registration prices (USD) per TLD.

These are typical registrar list prices — estimates only. Real prices vary
by registrar, promotions, and premium-domain status. Always confirm at
checkout before buying.
"""

TLD_PRICES = {
    # Popular generic
    "com": 11.99, "net": 12.49, "org": 11.49, "info": 4.99, "biz": 6.99,
    "name": 11.99, "pro": 5.99, "xyz": 2.99, "online": 2.49, "site": 1.99,
    "store": 3.99, "shop": 3.99, "website": 2.49, "space": 2.49,
    "tech": 9.99, "app": 14.99, "dev": 12.99, "io": 39.99, "ai": 68.99,
    "co": 12.99, "me": 8.99, "tv": 34.99, "cc": 12.99, "ws": 29.99,
    # Lifestyle / generic
    "blog": 8.99, "cloud": 19.99, "digital": 4.99, "agency": 4.99,
    "studio": 19.99, "design": 29.99, "media": 6.99, "news": 9.99,
    "live": 3.99, "world": 3.99, "life": 3.99, "today": 3.99,
    "guru": 5.99, "solutions": 5.99, "company": 4.99, "group": 4.99,
    "services": 5.99, "systems": 5.99, "zone": 5.99, "network": 4.99,
    "email": 3.99, "center": 4.99, "club": 3.99, "vip": 17.99,
    "fun": 1.99, "host": 29.99, "press": 29.99, "top": 1.99,
    "link": 3.99, "click": 3.99, "work": 4.99, "software": 13.99,
    "agency": 4.99, "market": 6.99, "social": 6.99, "community": 5.99,
    # Business-ish
    "business": 4.99, "consulting": 9.99, "finance": 9.99, "legal": 9.99,
    "ventures": 9.99, "partners": 9.99, "capital": 9.99, "exchange": 9.99,
    "academy": 8.99, "school": 6.99, "education": 7.99, "training": 9.99,
    "health": 9.99, "care": 6.99, "fitness": 6.99, "photography": 9.99,
    "art": 5.99, "music": 6.99, "game": 9.99, "games": 5.99,
    "travel": 9.99, "food": 6.99, "restaurant": 9.99, "cafe": 6.99,
    # Country-code (registration TLD)
    "us": 9.99, "uk": 8.99, "ca": 12.99, "de": 9.99, "in": 7.99,
    "eu": 8.99, "fr": 9.99, "nl": 9.99, "au": 12.99, "jp": 14.99,
    "sg": 39.99, "bd": 25.99, "pk": 9.99, "id": 19.99, "vn": 29.99,
}


def price_for(tld):
    """Estimated first-year USD price for a TLD, or None if unknown."""
    if not tld:
        return None
    key = tld.strip().lstrip(".").lower()
    if key in TLD_PRICES:
        return TLD_PRICES[key]
    # Multi-part TLDs like co.uk: fall back to the registry TLD.
    last = key.split(".")[-1]
    return TLD_PRICES.get(last)


def format_price(price):
    return f"${price:.2f}/yr" if price is not None else "-"
