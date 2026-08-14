"""Backfill a few weeks of synthetic price history per variant.

A fresh import gives every variant exactly one price_snapshot, which is
enough to satisfy M2's idempotency check but not enough to demo M7's price
chart and discount-honesty check ("was the list price ever actually
charged?"). This inserts 5-7 additional historical snapshots per variant,
dated over the past ~35 days, fluctuating around that variant's current
price. Safe to run once: skips any variant that already has more than one
snapshot.

Usage: python scripts/simulate_price_history.py
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import PriceSnapshot, Variant  # noqa: E402

random.seed(7)


def run():
    session = SessionLocal()
    try:
        variant_ids = session.scalars(select(Variant.id)).all()
        skipped = 0
        enriched = 0
        for variant_id in variant_ids:
            existing = session.scalars(
                select(PriceSnapshot).where(PriceSnapshot.variant_id == variant_id)
            ).all()
            if len(existing) > 1:
                skipped += 1
                continue

            current = existing[0]
            list_price = current.list_price_cents
            now = current.captured_at or datetime.now(timezone.utc)

            n_points = random.randint(5, 7)
            days_ago = sorted(random.sample(range(2, 35), n_points), reverse=True)
            for day in days_ago:
                # ~35% chance the list price was genuinely charged that day.
                if random.random() < 0.35:
                    price = list_price
                else:
                    price = round(list_price * random.uniform(0.55, 0.95))
                session.add(
                    PriceSnapshot(
                        variant_id=variant_id,
                        price_cents=price,
                        list_price_cents=list_price,
                        in_stock=random.random() > 0.05,
                        captured_at=now - timedelta(days=day, hours=random.randint(0, 23)),
                    )
                )
            enriched += 1
        session.commit()

        total_snapshots = session.scalar(select(func.count()).select_from(PriceSnapshot))
        print(f"enriched {enriched} variants, skipped {skipped} already-enriched, total snapshots: {total_snapshots}")
    finally:
        session.close()


if __name__ == "__main__":
    run()
