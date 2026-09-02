"""Import feeds into the database.

Idempotent: re-running this must not create duplicate variants (matched by
shop_id + shop_sku) or duplicate products (matched by normalized brand +
model_name + category + gender), but every row always appends a fresh
price_snapshot.

Real feeds are imported by default. The generated sample fixtures under
data/samples/ are opt-in via --with-samples: once a database holds real
affiliate data, silently mixing placeholder products back in on every
import is worse than useless — their picsum.photos images and invented
brands are indistinguishable from real rows in the UI.

Usage: python -m app.importers.run [--with-samples]
"""
import argparse
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

LIVE_FEEDS = [
    (
        "awin-live-unipolar",
        LIVE_DIR / "awin.csv",
        parse_awin_live_csv,
        {"name": "Unipolar DE", "slug": "unipolar-de", "affiliate_network": "Awin"},
    ),
]

SAMPLE_FEEDS = [
    (
        "awin",
        SAMPLES_DIR / "awin_jeans.csv",
        parse_awin_csv,
        {"name": "Awin Denim Store", "slug": "awin-denim-store", "affiliate_network": "Awin"},
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


def run_import(with_samples: bool = False) -> None:
    feeds = LIVE_FEEDS + SAMPLE_FEEDS if with_samples else LIVE_FEEDS
    session = SessionLocal()
    try:
        for key, path, parser, shop_meta in feeds:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-samples",
        action="store_true",
        help="also import the generated fixtures under data/samples/ (placeholder data)",
    )
    run_import(with_samples=parser.parse_args().with_samples)
