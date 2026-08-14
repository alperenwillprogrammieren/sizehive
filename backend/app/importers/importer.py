from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.importers.common import normalize
from app.models import PriceSnapshot, Product, Shop, Variant


def find_or_create_shop(session: Session, meta: dict) -> Shop:
    shop = session.scalars(select(Shop).where(Shop.slug == meta["slug"])).first()
    if shop is None:
        shop = Shop(**meta)
        session.add(shop)
        session.flush()
    return shop


def find_or_create_product(session: Session, row: dict) -> Product:
    """Match products by normalized (brand, model_name, category, gender).

    This merges the same listing across re-runs of one feed. It will only
    merge the *same* product across two different shops if both happen to
    spell the brand identically — real cross-shop brand-alias resolution
    is M3's job, not this importer's.
    """
    brand_norm = normalize(row["brand"])
    model_norm = normalize(row["model_name"])
    stmt = select(Product).where(
        func.lower(Product.brand) == brand_norm,
        func.lower(Product.model_name) == model_norm,
        Product.category == row["category"],
        Product.gender == row["gender"],
    )
    product = session.scalars(stmt).first()
    if product is None:
        product = Product(
            brand=row["brand"],
            model_name=row["model_name"],
            category=row["category"],
            gender=row["gender"],
            attributes={},
            attribute_sources={},
        )
        session.add(product)
        session.flush()
    return product


def find_or_create_variant(session: Session, shop: Shop, product: Product, row: dict) -> tuple[Variant, bool]:
    stmt = select(Variant).where(Variant.shop_id == shop.id, Variant.shop_sku == row["shop_sku"])
    variant = session.scalars(stmt).first()
    if variant is not None:
        return variant, False
    variant = Variant(
        product_id=product.id,
        shop_id=shop.id,
        shop_sku=row["shop_sku"],
        ean=row["ean"],
        size_raw=row["size_raw"],
        size_w=None,  # populated once the M3 size parser runs
        size_l=None,
        color=row["color"],
        url=row["deeplink_url"],
    )
    session.add(variant)
    session.flush()
    return variant, True


def import_row(session: Session, shop: Shop, row: dict) -> bool:
    """Import one normalized feed row. Returns True if a new variant was created.

    Always appends a price_snapshot, even for a variant that already
    existed — that append-only trail is how price history accrues.
    """
    product = find_or_create_product(session, row)
    variant, created = find_or_create_variant(session, shop, product, row)
    session.add(
        PriceSnapshot(
            variant_id=variant.id,
            price_cents=row["price_cents"],
            list_price_cents=row["list_price_cents"],
            in_stock=row["in_stock"],
        )
    )
    return created
