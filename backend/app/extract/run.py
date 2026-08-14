"""Apply the rule-based extractor to every product and persist attributes.

Usage: python -m app.extract.run
"""
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import SessionLocal
from app.extract.registry import get_extractor
from app.extract.report import print_report
from app.models import Product


def run_extraction() -> None:
    session = SessionLocal()
    try:
        products = list(session.scalars(select(Product)))
        for product in products:
            text = f"{product.brand} {product.model_name}. {product.description}"
            extracted = get_extractor(product.category).extract(text)
            for attr, result in extracted.items():
                product.attributes[attr] = result.value
                product.attribute_sources[attr] = {"source": result.source, "confidence": result.confidence}
            # JSONB columns are mutated in place; SQLAlchemy won't notice without this.
            flag_modified(product, "attributes")
            flag_modified(product, "attribute_sources")
        session.commit()

        print_report(products)
    finally:
        session.close()


if __name__ == "__main__":
    run_extraction()
