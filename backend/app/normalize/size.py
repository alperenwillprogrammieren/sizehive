"""Parse jeans waist/length size notations into (size_w, size_l).

Handles the notations affiliate feeds actually use: "W32/L34", "32/34",
"W 32 L 34", "32x34", and minor punctuation/case variants of those. Anything
else (a bare EU size, a letter size, free text) is not guessable without
a size-system conversion table, which is explicitly out of MVP scope — it
is logged and reported as unparsed rather than silently dropped or guessed.
"""
import logging
import re

logger = logging.getLogger("sizehive.normalize.size")

_W_L_PATTERN = re.compile(r"^W\s*(\d{2})\s*[/\-]?\s*L\s*(\d{2})$")
_NUMERIC_PATTERN = re.compile(r"^(\d{2})\s*[/X×\-]\s*(\d{2})$")


def parse_size(raw: str) -> tuple[int | None, int | None]:
    """Return (size_w, size_l), or (None, None) if unparseable."""
    s = (raw or "").strip().upper()

    m = _W_L_PATTERN.match(s)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = _NUMERIC_PATTERN.match(s)
    if m:
        return int(m.group(1)), int(m.group(2))

    logger.warning("unparseable size: %r", raw)
    return None, None
