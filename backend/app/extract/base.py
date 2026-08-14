"""Extractor interface all Kür-attribute extractors implement.

Keeping this as a narrow Protocol is what M4 means by "austauschbare
Komponente": app.extract.rules.RuleBasedExtractor is the only
implementation today, but an LLM-backed extractor can be dropped in next
to it later — same input, same output shape, same `source` values it's
allowed to write (just "llm" instead of "rule") — without touching
anything that calls extract().
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractedAttribute:
    value: object
    source: str  # "rule" | "llm"
    confidence: float


class AttributeExtractor(Protocol):
    def extract(self, text: str) -> dict[str, ExtractedAttribute]:
        """Return a subset of the Kür attribute taxonomy found in `text`."""
        ...
