"""Import all local sample feeds into the database.

Idempotent: re-running this must not create duplicate variants (matched by
shop_id + shop_sku) or duplicate products (matched by normalized brand +
model_name + category + gender), but every row always appends a fresh
price_snapshot.

Usage: python -m app.importers.run
"""
from pathlib import Path

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.importers.adapters import (
    parse_awin_csv,
    parse_awin_live_csv,
    parse_belboon_csv,
    parse_tradedoubler_xml,
)
from app.importers.importer import find_or_create_shop, import_row
from app.models import PriceSnapshot, Variant

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"
LIVE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "live"

FEEDS = [
    (
        "awin",
        SAMPLES_DIR / "awin_jeans.csv",
        parse_awin_csv,
        {"name": "Awin Denim Store", "slug": "awin-denim-store", "affiliate_network": "Awin"},
    ),
    (
        "awin-live-unipolar",
        LIVE_DIR / "awin.csv",
        parse_awin_live_csv,
        {"name": "Unipolar DE", "slug": "unipolar-de", "affiliate_network": "Awin"},
    ),
    (
        "belboon",
        SAMPLES_DIR / "belboon_jeans.csv",
        parse_belboon_csv,
        {"name": "Belboon Fashion Outlet", "slug": "belboon-fashion-outlet", "affiliate_network": "Belboon"},
    ),
    (
        "tradedoubler",
        SAMPLES_DIR / "tradedoubler_jeans.xml",
        parse_tradedoubler_xml,
        {"name": "Tradedoubler Streetwear", "slug": "tradedoubler-streetwear", "affiliate_network": "Tradedoubler"},
    ),
]


def run_import() -> None:
    session = SessionLocal()
    try:
        for key, path, parser, shop_meta in FEEDS:
            if not path.exists():
                print(f"[{key}] skipped, file not found: {path}")
                continue
            shop = find_or_create_shop(session, shop_meta)
            session.commit()

            rows = 0
            new_variants = 0
            for row in parser(path):
                rows += 1
                if import_row(session, shop, row):
                    new_variants += 1
            session.commit()
            print(f"[{key}] {rows} rows read, {new_variants} new variants")

        total_variants = session.scalar(select(func.count()).select_from(Variant))
        total_snapshots = session.scalar(select(func.count()).select_from(PriceSnapshot))
        print(f"totals: {total_variants} variants, {total_snapshots} price snapshots")
    finally:
        session.close()


if __name__ == "__main__":
    run_import()
