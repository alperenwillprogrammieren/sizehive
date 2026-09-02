"""Helpers shared by every category's rule-based extractor."""
import re
from functools import lru_cache

COTTON_RE = re.compile(r"(\d{1,3})\s*%\s*(?:baumwolle|cotton)", re.IGNORECASE)
ELASTANE_RE = re.compile(r"(\d{1,3})\s*%\s*(?:elasthan|elastane)", re.IGNORECASE)

# Named fibres, most specific first — "recycelte Baumwolle" and
# "Bio-Baumwolle" must both win over plain "Baumwolle".
#
# This is deliberately separate from extract_material(): that one parses
# *compositions* ("98 % Baumwolle, 2 % Elasthan") and feeds the cotton_min
# filter. Real shop copy usually names a fibre without ever giving a
# percentage ("T-Shirt aus Ecovero"), which the composition parser can't
# see — so `fiber` captures that as a plain, facetable scalar.
FIBER_KEYWORDS: dict[str, list[str]] = {
    "recycled_cotton": ["recycelter baumwolle", "recycelte baumwolle", "recycled cotton"],
    "organic_cotton": ["bio-baumwolle", "bio baumwolle", "organic cotton", "biobaumwolle"],
    "tencel": ["tencel", "lyocell"],
    "ecovero": ["ecovero"],
    "linen": ["leinen", "linen"],
    "hemp": ["hanf", "hemp"],
    "modal": ["modal"],
    "wool": ["merinowolle", "merino", "wolle", "woll-", "wool"],
    "leather": ["wildleder", "leder", "leather"],
    "cotton": ["baumwolle", "cotton"],
}

# Only claims that are verifiable or factual. Bare marketing adjectives
# ("nachhaltig") are deliberately NOT tags here: mixing an unverifiable
# self-description in with GOTS would make the filter mean nothing, and
# this project's whole pitch is not repeating what a shop asserts about
# itself (see the measured-vs-claimed discount handling).
SUSTAINABILITY_KEYWORDS: dict[str, list[str]] = {
    "gots": ["gots"],
    "organic_cotton": ["bio-baumwolle", "bio baumwolle", "organic cotton", "biobaumwolle"],
    "organic_certified": ["bio-zertifiziert", "biozertifiziert", "bio zertifiziert"],
    "fair_trade": ["fair produziert", "fairtrade", "fair trade", "fair wear", "fair"],
    "vegan": ["vegan"],
    "recycled": ["recycelt", "recycled"],
}


@lru_cache(maxsize=4096)
def _phrase_pattern(phrase: str) -> re.Pattern:
    return re.compile(r"\b" + re.escape(phrase))


def phrase_in(text_lower: str, phrase: str) -> bool:
    """Substring match anchored at a word start.

    Plain `in` is unsafe for German: compounds prepend, so "wolle" matches
    inside "Baumwolle" and a cotton shirt gets tagged wool. Anchoring the
    *start* of the phrase to a word boundary fixes that while still
    allowing the suffixes German inflection appends — "recycelt" has to go
    on matching "recycelter", so the end deliberately stays unanchored.
    """
    return _phrase_pattern(phrase).search(text_lower) is not None


def match_keywords(text_lower: str, keywords: dict[str, list[str]]) -> tuple[str, float] | None:
    """First matching value + confidence, or None. Longer/multi-word phrases score higher."""
    for value, phrases in keywords.items():
        for phrase in phrases:
            if phrase_in(text_lower, phrase):
                confidence = 0.9 if " " in phrase or "-" in phrase else 0.65
                return value, confidence
    return None


def extract_fiber(text_lower: str) -> tuple[str, float] | None:
    """Primary named fibre, or None. Scalar so it stays facetable."""
    return match_keywords(text_lower, FIBER_KEYWORDS)


def extract_sustainability(text_lower: str) -> list[str]:
    """All matching sustainability tags (a product can be both GOTS and vegan)."""
    return [
        tag
        for tag, phrases in SUSTAINABILITY_KEYWORDS.items()
        if any(phrase_in(text_lower, phrase) for phrase in phrases)
    ]


def extract_material(text_lower: str) -> dict | None:
    cotton = COTTON_RE.search(text_lower)
    elastane = ELASTANE_RE.search(text_lower)
    if not cotton and not elastane:
        return None
    material = {}
    if cotton:
        material["cotton_pct"] = int(cotton.group(1))
    if elastane:
        material["elastane_pct"] = int(elastane.group(1))
    return material
