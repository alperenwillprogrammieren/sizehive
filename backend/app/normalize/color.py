"""Map German/English color spellings to a canonical color slug."""
import logging

logger = logging.getLogger("sizehive.normalize.color")

CANONICAL_COLORS: dict[str, list[str]] = {
    "dark_blue": ["dunkelblau", "dunkel blau", "DUNKELBLAU", "dark blue", "navy", "navy blue"],
    "light_blue": ["hellblau", "hell blau", "HELLBLAU", "light blue", "sky blue"],
    "mid_blue": ["mittelblau", "mittel blau", "MITTELBLAU", "mid blue", "medium blue"],
    "black": ["schwarz", "SCHWARZ", "black"],
    "grey": ["grau", "GRAU", "grey", "gray"],
    "indigo": ["indigo", "INDIGO"],
    "khaki": ["khaki", "KHAKI", "beige-khaki"],
}

_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias.strip().lower(): canonical
    for canonical, aliases in CANONICAL_COLORS.items()
    for alias in [canonical, *aliases]
}


def normalize_color(raw: str) -> str:
    """Return the canonical color slug, or the trimmed lowercased input if unknown."""
    key = (raw or "").strip().lower()
    canonical = _ALIAS_TO_CANONICAL.get(key)
    if canonical is None:
        logger.warning("unmapped color spelling: %r", raw)
        return key
    return canonical
