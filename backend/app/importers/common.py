import re


def normalize(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def derive_model_name(title: str, brand: str) -> str:
    """Best-effort strip of the brand prefix from a combined title string.

    Feeds here only expose a combined "brand + model" title, not the two
    separately. This heuristic is enough for M2; robust brand-alias
    resolution belongs to the M3 normalizer.
    """
    title = title.strip()
    brand = brand.strip()
    if title.lower().startswith(brand.lower()):
        rest = title[len(brand):].strip()
        return rest or title
    return title


def parse_price_cents(raw: str, decimal_sep: str = ".") -> int:
    if decimal_sep == ",":
        raw = raw.replace(".", "").replace(",", ".")
    return round(float(raw) * 100)
