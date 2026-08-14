"""Category -> extractor lookup. Adding a category means adding one entry
here (plus app.taxonomy) and writing the extractor class — nothing else in
the extraction pipeline changes.
"""
from app.extract.base import AttributeExtractor
from app.extract.rules import RuleBasedExtractor
from app.extract.sneakers import SneakerExtractor
from app.extract.tshirts import TShirtExtractor


class NullExtractor:
    """Used for categories without a dedicated extractor yet."""

    def extract(self, text: str) -> dict:
        return {}


_EXTRACTORS: dict[str, AttributeExtractor] = {
    "Herrenjeans": RuleBasedExtractor(),
    "T-Shirts": TShirtExtractor(),
    "Sneaker": SneakerExtractor(),
}
_FALLBACK = NullExtractor()


def get_extractor(category: str) -> AttributeExtractor:
    return _EXTRACTORS.get(category, _FALLBACK)
