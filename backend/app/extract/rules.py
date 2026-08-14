"""Regex/keyword rule-based extractor for the Kür (derived) jeans attributes.

Scans free-text (product title + description) for known German/English
phrases per attribute. Longer, more specific phrases are checked before
short generic words and win a higher confidence score, since a hit on
"stonewashed" is a lot more trustworthy than a hit on a single generic
word like "raw".
"""
from app.extract.base import ExtractedAttribute
from app.extract.common import extract_material, match_keywords

# canonical value -> phrases that imply it, most specific first
FIT_KEYWORDS: dict[str, list[str]] = {
    "wide leg": ["wide leg", "weites hosenbein", "ausgestelltes bein"],
    "baggy": ["baggy fit", "baggy", "extra weit geschnitten"],
    "skinny": ["skinny fit", "skinny cut", "skinny"],
    "slim": ["slim fit", "slim cut", "slim tapered", "schmale passform", "slim"],
    "loose": ["loose fit", "lockere passform", "weites bein", "loose"],
    "relaxed": ["relaxed fit", "entspannte passform", "relaxed"],
    "straight": ["straight fit", "straight leg", "gerades bein", "straight"],
    "regular": ["regular fit", "klassische passform", "regular"],
}
RISE_KEYWORDS: dict[str, list[str]] = {
    "high": ["high waist", "hohe bundhöhe", "high rise"],
    "low": ["low waist", "tief sitzend", "low rise"],
    "mid": ["mid waist", "normale bundhöhe", "mid rise"],
}
LEG_SHAPE_KEYWORDS: dict[str, list[str]] = {
    "bootcut": ["bootcut", "leicht ausgestellt"],
    "flared": ["flared", "schlaghose"],
    "tapered": ["tapered leg", "verjüngtes bein", "tapered"],
    "straight": ["straight leg", "gerades bein"],
}
WASH_KEYWORDS: dict[str, list[str]] = {
    "stonewashed": ["stonewashed", "stone washed"],
    "destroyed": ["destroyed look", "destroyed", "mit rissen"],
    "black": ["black denim", "schwarz"],
    "raw": ["raw denim", "ungewaschen", "raw"],
    "light": ["light wash", "hell gewaschen"],
    "dark": ["dark wash", "dunkel gewaschen"],
    "mid": ["mid wash", "mittlere waschung"],
    "used": ["used look", "used waschung"],
}
CLOSURE_KEYWORDS: dict[str, list[str]] = {
    "button_fly": ["knopfleiste", "button fly"],
    "zip_fly": ["reißverschluss", "zip fly", "zipper"],
}
SUSTAINABILITY_KEYWORDS: dict[str, list[str]] = {
    "gots": ["gots"],
    "organic_cotton": ["bio-baumwolle", "organic cotton", "bio baumwolle"],
}

import re

_POCKETS_RE = re.compile(r"(\d{1,2})\s*(?:taschen|pockets)", re.IGNORECASE)


class RuleBasedExtractor:
    """Keyword/regex extractor. Implements app.extract.base.AttributeExtractor."""

    def extract(self, text: str) -> dict[str, ExtractedAttribute]:
        text_lower = (text or "").lower()
        result: dict[str, ExtractedAttribute] = {}

        for attr, keywords in (
            ("fit", FIT_KEYWORDS),
            ("rise", RISE_KEYWORDS),
            ("leg_shape", LEG_SHAPE_KEYWORDS),
            ("wash", WASH_KEYWORDS),
            ("closure", CLOSURE_KEYWORDS),
        ):
            hit = match_keywords(text_lower, keywords)
            if hit:
                value, confidence = hit
                result[attr] = ExtractedAttribute(value=value, source="rule", confidence=confidence)

        material = extract_material(text_lower)
        if material:
            result["material"] = ExtractedAttribute(value=material, source="rule", confidence=0.95)
            result["stretch"] = ExtractedAttribute(
                value="elastane_pct" in material or "stretch" in text_lower, source="rule", confidence=0.85,
            )
        elif "stretch" in text_lower:
            result["stretch"] = ExtractedAttribute(value=True, source="rule", confidence=0.7)

        pockets = _POCKETS_RE.search(text_lower)
        if pockets:
            result["pockets"] = ExtractedAttribute(value=int(pockets.group(1)), source="rule", confidence=0.75)

        sustainability_tags = [
            tag for tag, phrases in SUSTAINABILITY_KEYWORDS.items() if any(p in text_lower for p in phrases)
        ]
        if sustainability_tags:
            result["sustainability"] = ExtractedAttribute(
                value=sustainability_tags, source="rule", confidence=0.85,
            )

        return result
