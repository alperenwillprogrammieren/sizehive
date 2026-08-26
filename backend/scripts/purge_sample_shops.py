"""One-off cleanup: remove the three sample-fixture shops (and everything
that hangs off them) from a database that now also holds real feed data,
without touching products that real shops still reference.

Usage: python scripts/purge_sample_shops.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import PriceSnapshot, Product, Shop, Variant  # noqa: E402

SAMPLE_SHOP_SLUGS = ["awin-denim-store", "belboon-fashion-outlet", "tradedoubler-streetwear"]


def main() -> None:
    session = SessionLocal()
    try:
        shops = session.scalars(select(Shop).where(Shop.slug.in_(SAMPLE_SHOP_SLUGS))).all()
        if not shops:
            print("No sample shops found — nothing to do.")
            return
        shop_ids = [s.id for s in shops]

        variant_ids = session.scalars(select(Variant.id).where(Variant.shop_id.in_(shop_ids))).all()
        product_ids = set(session.scalars(select(Variant.product_id).where(Variant.shop_id.in_(shop_ids))))

        snapshot_count = session.query(PriceSnapshot).filter(PriceSnapshot.variant_id.in_(variant_ids)).delete(
            synchronize_session=False
        )
        variant_count = session.query(Variant).filter(Variant.shop_id.in_(shop_ids)).delete(
            synchronize_session=False
        )

        # Only drop products left with zero variants — a product could in
        # principle still be referenced by a real shop's variant.
        orphaned_product_ids = [
            pid for pid in product_ids
            if session.scalar(select(Variant.id).where(Variant.product_id == pid).limit(1)) is None
        ]
        product_count = 0
        if orphaned_product_ids:
            product_count = session.query(Product).filter(Product.id.in_(orphaned_product_ids)).delete(
                synchronize_session=False
            )

        for shop in shops:
            session.delete(shop)

        session.commit()
        print(f"Deleted: {len(shops)} shops, {variant_count} variants, "
              f"{snapshot_count} price snapshots, {product_count} orphaned products")
    finally:
        session.close()


if __name__ == "__main__":
    main()
