"""Map inconsistent brand spellings from different feeds to one canonical name.

Real affiliate feeds spell the same brand differently ("Levi's" vs "LEVIS"
vs "Levi Strauss & Co."). This is a static alias table rather than fuzzy
matching: predictable and testable, at the cost of needing new brands/
spellings added by hand as they're seen. `sample feed generator
(scripts/generate_sample_feeds.py) reuses this table so the messy test data
and the parser that cleans it up stay in sync.
"""
import logging

logger = logging.getLogger("sizehive.normalize.brand")

# canonical brand -> known raw spellings (canonical itself is always accepted too)
CANONICAL_BRANDS: dict[str, list[str]] = {
    "Levi's": ["Levi's", "LEVIS", "Levi Strauss & Co."],
    "Wrangler": ["Wrangler", "WRANGLER"],
    "Lee": ["Lee", "LEE Jeans"],
    "Diesel": ["Diesel", "DIESEL"],
    "Tommy Hilfiger": ["Tommy Hilfiger", "Tommy Hilfiger Denim", "TOMMY HILFIGER"],
    "Calvin Klein": ["Calvin Klein", "Calvin Klein Jeans", "CK"],
    "G-Star": ["G-Star", "G-Star RAW", "G STAR"],
    "Pepe Jeans": ["Pepe Jeans", "PEPE JEANS LONDON"],
    "Jack & Jones": ["Jack & Jones", "JACK JONES", "Jack&Jones"],
    "Nudie Jeans": ["Nudie Jeans", "NUDIE"],
    "Replay": ["Replay", "REPLAY"],
    "BOSS": ["BOSS", "Hugo Boss"],
}

_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias.strip().lower(): canonical
    for canonical, aliases in CANONICAL_BRANDS.items()
    for alias in [canonical, *aliases]
}


def normalize_brand(raw: str) -> str:
    """Return the canonical brand name, or the trimmed input if unknown."""
    key = (raw or "").strip().lower()
    canonical = _ALIAS_TO_CANONICAL.get(key)
    if canonical is None:
        logger.warning("unmapped brand spelling: %r", raw)
        return (raw or "").strip()
    return canonical
