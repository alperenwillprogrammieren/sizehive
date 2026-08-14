"""Category registry — this is what "new category = configuration, not schema
change" means in practice: add an entry here plus an extractor implementing
app.extract.base.AttributeExtractor, and the search/facets API and the
extraction pipeline pick it up automatically. No DB migration, no new API
parameters.
"""

CATEGORIES: dict[str, dict] = {
    "Herrenjeans": {"gender": "male", "extractor": "jeans"},
    "T-Shirts": {"gender": "unisex", "extractor": "tshirts"},
    "Sneaker": {"gender": "unisex", "extractor": "sneakers"},
}


def gender_for_category(category: str) -> str:
    return CATEGORIES.get(category, {}).get("gender", "unisex")
