from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.importers.common import normalize
from app.models import PriceSnapshot, Product, Shop, Variant
from app.normalize.brand import normalize_brand
from app.normalize.color import normalize_color
from app.normalize.size import parse_size


def find_or_create_shop(session: Session, meta: dict) -> Shop:
    shop = session.scalars(select(Shop).where(Shop.slug == meta["slug"])).first()
    if shop is None:
        shop = Shop(**meta)
        session.add(shop)
        session.flush()
    return shop


def find_or_create_product(session: Session, row: dict) -> Product:
    """Match products by normalized (brand, model_name, category, gender).

    `row["brand"]` is expected to already be canonicalized by
    app.normalize.brand.normalize_brand (see import_row) — that's what lets
    the same product sold by two shops under differently spelled brand
    names merge into one product row here. model_name still only merges on
    exact (case/whitespace-insensitive) text match.
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
            description=row.get("description", ""),
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
    size_w, size_l = parse_size(row["size_raw"])
    variant = Variant(
        product_id=product.id,
        shop_id=shop.id,
        shop_sku=row["shop_sku"],
        ean=row["ean"],
        size_raw=row["size_raw"],
        size_w=size_w,
        size_l=size_l,
        color=normalize_color(row["color"]),
        url=row["deeplink_url"],
        image_url=row.get("image_url", ""),
    )
    session.add(variant)
    session.flush()
    return variant, True


def import_row(session: Session, shop: Shop, row: dict) -> bool:
    """Import one normalized feed row. Returns True if a new variant was created.

    Always appends a price_snapshot, even for a variant that already
    existed — that append-only trail is how price history accrues.
    """
    row = {**row, "brand": normalize_brand(row["brand"])}
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
