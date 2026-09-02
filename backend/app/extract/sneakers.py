"""Rule-based extractor for the Sneaker category."""
from app.extract.base import ExtractedAttribute
from app.extract.common import extract_sustainability, match_keywords

# Real sustainable-footwear copy names the upper by fibre ("veganer
# Sneaker", "aus recycelter Baumwolle", "Tencel Sneaker") far more often
# than by the classic sneaker materials this list originally held — hence
# the additions below, all taken from the live catalogue's own wording.
UPPER_MATERIAL_KEYWORDS: dict[str, list[str]] = {
    "suede": ["suede", "wildleder"],
    "vegan": ["veganer", "vegane", "vegan"],
    "recycled_cotton": ["recycelter baumwolle", "recycelte baumwolle", "recycled cotton"],
    "tencel": ["tencel", "lyocell"],
    "wool": ["woll-sneaker", "wollsneaker", "merinowolle", "merino", "wolle", "wool"],
    "cotton": ["bio-baumwolle", "baumwolle", "canvas upper", "canvas"],
    "leather": ["leather upper", "leder-obermaterial", "vegetabil", "leder"],
    "mesh": ["mesh upper", "mesh-obermaterial", "mesh"],
    "synthetic": ["synthetic upper", "synthetik-obermaterial", "synthetik"],
}
SOLE_KEYWORDS: dict[str, list[str]] = {
    "air": ["air-cushioning", "air sole", "luftpolster"],
    "foam": ["foam sole", "foam-sohle", "schaumstoffsohle"],
    "chunky": ["dicker sohle", "dicke sohle", "plateausohle", "chunky"],
    "rubber": ["rubber sole", "gummisohle", "kautschuksohle", "naturkautschuk"],
}
CLOSURE_KEYWORDS: dict[str, list[str]] = {
    "velcro": ["velcro", "klettverschluss"],
    "slip_on": ["slip-on", "slip on", "ohne verschluss"],
    # "Schnürschuh" is what the catalogue says; "Schnürsenkel" (the lace
    # itself) almost never appears in a product name.
    "laces": ["schnürschuh", "schnürung", "schnürsenkel", "lace-up", "laces"],
}
STYLE_KEYWORDS: dict[str, list[str]] = {
    # Unhyphenated "Low Top" is the spelling actually used in the feed;
    # matching only "low-top" missed essentially all of them.
    "high_top": ["high-top", "high top", "hoher schaft", "hightop"],
    "low_top": ["low-top", "low top", "niedriger schaft", "lowtop"],
}


class SneakerExtractor:
    """Implements app.extract.base.AttributeExtractor for Sneaker."""

    def extract(self, text: str) -> dict[str, ExtractedAttribute]:
        text_lower = (text or "").lower()
        result: dict[str, ExtractedAttribute] = {}

        for attr, keywords in (
            ("upper_material", UPPER_MATERIAL_KEYWORDS),
            ("sole_type", SOLE_KEYWORDS),
            ("closure_type", CLOSURE_KEYWORDS),
            ("style", STYLE_KEYWORDS),
        ):
            hit = match_keywords(text_lower, keywords)
            if hit:
                value, confidence = hit
                result[attr] = ExtractedAttribute(value=value, source="rule", confidence=confidence)

        sustainability_tags = extract_sustainability(text_lower)
        if sustainability_tags:
            result["sustainability"] = ExtractedAttribute(
                value=sustainability_tags, source="rule", confidence=0.85,
            )

        return result
