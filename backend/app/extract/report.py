"""Coverage report: per category, what fraction of its products have each
Kür attribute. Grouped by category because different categories have
different attribute vocabularies (a T-Shirt has no "wash") — a single
blended global number would hide exactly the thing this report exists to
surface, per spec: "wo die Extraktion schwächelt".
"""
from collections import Counter, defaultdict

from app.models import Product


def coverage_report(products: list[Product]) -> dict[str, dict[str, float]]:
    """category -> {attribute: coverage_fraction}. Attribute keys are discovered
    per category from whatever extractor actually wrote into `attributes` —
    nothing hardcoded, so a new category needs no change here."""
    by_category: dict[str, list[Product]] = defaultdict(list)
    for product in products:
        by_category[product.category].append(product)

    report: dict[str, dict[str, float]] = {}
    for category, cat_products in by_category.items():
        total = len(cat_products)
        keys = sorted({key for p in cat_products for key in p.attributes.keys()})
        counts = Counter()
        for p in cat_products:
            for key in keys:
                if key in p.attributes:
                    counts[key] += 1
        report[category] = {key: counts[key] / total for key in keys} if total else {}
    return report


def print_report(products: list[Product]) -> None:
    report = coverage_report(products)
    print(f"attribute coverage over {len(products)} products, by category:")
    for category, coverage in report.items():
        n = sum(1 for p in products if p.category == category)
        print(f"  {category} ({n} products):")
        for attr, pct in coverage.items():
            print(f"    {attr:15s} {pct * 100:5.1f}%")
