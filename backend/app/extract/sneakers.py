"""Rule-based extractor for the Sneaker category."""
from app.extract.base import ExtractedAttribute
from app.extract.common import match_keywords

UPPER_MATERIAL_KEYWORDS: dict[str, list[str]] = {
    "leather": ["leather upper", "leder-obermaterial", "leder"],
    "suede": ["suede", "wildleder"],
    "mesh": ["mesh upper", "mesh-obermaterial", "mesh"],
    "canvas": ["canvas upper", "canvas-obermaterial", "canvas"],
    "synthetic": ["synthetic upper", "synthetik-obermaterial", "synthetik"],
}
SOLE_KEYWORDS: dict[str, list[str]] = {
    "air": ["air-cushioning", "air sole", "luftpolster"],
    "foam": ["foam sole", "foam-sohle", "schaumstoffsohle"],
    "rubber": ["rubber sole", "gummisohle"],
}
CLOSURE_KEYWORDS: dict[str, list[str]] = {
    "velcro": ["velcro", "klettverschluss"],
    "slip_on": ["slip-on", "slip on", "ohne verschluss"],
    "laces": ["schnürsenkel", "lace-up", "laces"],
}
STYLE_KEYWORDS: dict[str, list[str]] = {
    "high_top": ["high-top", "hoher schaft"],
    "low_top": ["low-top", "niedriger schaft"],
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

        return result
