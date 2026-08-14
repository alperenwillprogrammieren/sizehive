"""Helpers shared by every category's rule-based extractor."""
import re

COTTON_RE = re.compile(r"(\d{1,3})\s*%\s*(?:baumwolle|cotton)", re.IGNORECASE)
ELASTANE_RE = re.compile(r"(\d{1,3})\s*%\s*(?:elasthan|elastane)", re.IGNORECASE)


def match_keywords(text_lower: str, keywords: dict[str, list[str]]) -> tuple[str, float] | None:
    """First matching value + confidence, or None. Longer/multi-word phrases score higher."""
    for value, phrases in keywords.items():
        for phrase in phrases:
            if phrase in text_lower:
                confidence = 0.9 if " " in phrase or "-" in phrase else 0.65
                return value, confidence
    return None


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
