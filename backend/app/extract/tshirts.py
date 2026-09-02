"""Rule-based extractor for the T-Shirts category.

Same mechanism as app.extract.rules.RuleBasedExtractor (jeans), just a
different keyword taxonomy — this is the proof that adding a category is
"write one extractor", not "touch the pipeline".
"""
from app.extract.base import ExtractedAttribute
from app.extract.common import (
    extract_fiber,
    extract_material,
    extract_sustainability,
    match_keywords,
)

FIT_KEYWORDS: dict[str, list[str]] = {
    "oversized": ["oversized", "oversize fit", "extra weit geschnitten"],
    "loose": ["loose fit", "lockere passform"],
    "boxy": ["boxy fit", "boxy"],
    "slim": ["slim fit", "schmale passform", "slim"],
    "relaxed": ["relaxed fit", "entspannte passform", "relaxed"],
    "regular": ["regular fit", "klassische passform", "regular"],
}
SLEEVE_KEYWORDS: dict[str, list[str]] = {
    "sleeveless": ["sleeveless", "ärmellos", "tank top"],
    "long": ["long sleeve", "langarm"],
    "short": ["short sleeve", "kurzarm"],
}
NECKLINE_KEYWORDS: dict[str, list[str]] = {
    "v_neck": ["v-neck", "v-ausschnitt"],
    "polo": ["polo kragen", "polo collar", "polokragen"],
    "boat": ["u-boot-ausschnitt", "boat neck"],
    "crew": ["crew neck", "rundhalsausschnitt", "rundhals"],
}
PRINT_KEYWORDS: dict[str, list[str]] = {
    "graphic": ["graphic print", "grafik-print", "print-shirt"],
    "logo": ["logo print", "logo-print", "markenlogo"],
    "striped": ["striped", "gestreift", "streifen"],
    "plain": ["plain", "unifarben", "einfarbig"],
}


class TShirtExtractor:
    """Implements app.extract.base.AttributeExtractor for T-Shirts."""

    def extract(self, text: str) -> dict[str, ExtractedAttribute]:
        text_lower = (text or "").lower()
        result: dict[str, ExtractedAttribute] = {}

        for attr, keywords in (
            ("fit", FIT_KEYWORDS),
            ("sleeve", SLEEVE_KEYWORDS),
            ("neckline", NECKLINE_KEYWORDS),
            ("print", PRINT_KEYWORDS),
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

        fiber = extract_fiber(text_lower)
        if fiber:
            value, confidence = fiber
            result["fiber"] = ExtractedAttribute(value=value, source="rule", confidence=confidence)

        sustainability_tags = extract_sustainability(text_lower)
        if sustainability_tags:
            result["sustainability"] = ExtractedAttribute(
                value=sustainability_tags, source="rule", confidence=0.85,
            )

        return result
