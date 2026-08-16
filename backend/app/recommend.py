"""Scoring for "ähnliche Artikel".

The point of sizehive is that garments are described by many attributes, so
similarity here is attribute overlap first and price proximity second —
not a collaborative-filtering signal (there are no users' purchase
histories) and not brand matching (finding the *same* thing at another shop
is already what product matching does at import time).

Pure functions, no ORM: the ranking rules are unit-testable, and the
endpoint only supplies candidates.
"""
from dataclasses import dataclass

#: Attributes whose values aren't flat scalars (material is a nested object,
#: sustainability a tag list). Same exclusion the facets use — comparing them
#: needs their own semantics, and equality on a dict would be noise.
NON_SCALAR_ATTRS = {"material", "sustainability"}

#: Attribute agreement dominates; price proximity only breaks ties among
#: articles that already share a description.
ATTRIBUTE_WEIGHT = 0.75
PRICE_WEIGHT = 0.25


@dataclass(frozen=True)
class Similarity:
    score: float
    shared_attributes: list[str]


def _comparable(attributes: dict) -> dict:
    return {
        key: value
        for key, value in attributes.items()
        if key not in NON_SCALAR_ATTRS and isinstance(value, (str, bool, int, float))
    }


def price_proximity(base_cents: int, other_cents: int) -> float:
    """1.0 at an identical price, decaying to 0.0 at double or nothing."""
    if base_cents <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(other_cents - base_cents) / base_cents)


def similarity(base_attrs: dict, base_cents: int, other_attrs: dict, other_cents: int) -> Similarity:
    base = _comparable(base_attrs)
    other = _comparable(other_attrs)

    overlap = [key for key in base if key in other]
    shared = [key for key in overlap if base[key] == other[key]]
    # No attributes in common at all (different category vocabularies, or an
    # article nothing was extracted from): price alone shouldn't imply
    # similarity, so the attribute term stays 0 rather than defaulting to 1.
    attribute_score = len(shared) / len(overlap) if overlap else 0.0

    score = ATTRIBUTE_WEIGHT * attribute_score + PRICE_WEIGHT * price_proximity(base_cents, other_cents)
    return Similarity(score=round(score, 4), shared_attributes=sorted(shared))
