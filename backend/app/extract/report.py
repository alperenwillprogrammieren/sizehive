"""Coverage report: for each Kür attribute, what fraction of products have it."""
from collections import Counter

from app.models import Product

TRACKED_ATTRIBUTES = [
    "fit", "rise", "leg_shape", "wash", "material", "stretch", "closure", "pockets", "sustainability",
]


def coverage_report(products: list[Product]) -> dict[str, float]:
    total = len(products)
    if total == 0:
        return {attr: 0.0 for attr in TRACKED_ATTRIBUTES}
    counts = Counter()
    for product in products:
        for attr in TRACKED_ATTRIBUTES:
            if attr in product.attributes:
                counts[attr] += 1
    return {attr: counts[attr] / total for attr in TRACKED_ATTRIBUTES}


def print_report(products: list[Product]) -> None:
    total = len(products)
    report = coverage_report(products)
    print(f"attribute coverage over {total} products:")
    for attr, pct in report.items():
        print(f"  {attr:15s} {pct * 100:5.1f}%")

    both_fit_and_wash = sum(1 for p in products if "fit" in p.attributes and "wash" in p.attributes)
    pct = both_fit_and_wash / total * 100 if total else 0.0
    print(f"products with BOTH fit and wash: {both_fit_and_wash}/{total} ({pct:.1f}%)")
