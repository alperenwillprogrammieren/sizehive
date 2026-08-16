"""Deals and shop honesty — the two endpoints built on measured price history.

The premise: every shop advertises a discount against its own `list_price`,
a number it fully controls. Because `price_snapshot` is append-only, we can
ignore that claim and compute what actually happened instead:

- GET /api/deals ranks articles by how far the price fell against the price
  we recorded `window_days` ago. A struck-through list price never enters
  the ranking.
- GET /api/dashboard/shop-trust aggregates the per-article honesty check
  ("was the list price ever actually charged?") up to the shop level.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.api.schemas import DealItem, DealsResponse, ShopTrust, ShopTrustResponse
from app.api.search import _latest_price_subquery, _to_result_item, get_session
from app.models import PriceSnapshot, Product, Shop, Variant

router = APIRouter()


def _min_price_subquery():
    return (
        select(
            PriceSnapshot.variant_id.label("variant_id"),
            func.min(PriceSnapshot.price_cents).label("low_cents"),
        )
        .group_by(PriceSnapshot.variant_id)
        .subquery()
    )


def _price_at_or_before_subquery(cutoff: datetime):
    """The newest snapshot of each variant that is at least as old as `cutoff`
    — the "what did this cost back then?" reference point."""
    return (
        select(PriceSnapshot.variant_id, func.max(PriceSnapshot.captured_at).label("captured_at"))
        .where(PriceSnapshot.captured_at <= cutoff)
        .group_by(PriceSnapshot.variant_id)
        .subquery()
    )


@router.get("/deals", response_model=DealsResponse)
def deals(
    window_days: int = Query(7, ge=1, le=365, description="Compare against the price this many days ago"),
    min_drop_pct: float = Query(5.0, ge=0, le=100, description="Only drops of at least this size"),
    category: list[str] | None = Query(None, description="Repeat for multiple categories"),
    in_stock_only: bool = Query(True, description="An unbuyable deal is not a deal"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    latest = _latest_price_subquery()
    reference = _price_at_or_before_subquery(cutoff)
    lows = _min_price_subquery()

    Current = aliased(PriceSnapshot)
    Reference = aliased(PriceSnapshot)

    # Float multiplication first: price_cents are integers, and integer
    # division would floor every drop to 0.
    drop_pct = (Reference.price_cents - Current.price_cents) * 100.0 / Reference.price_cents

    stmt = (
        select(Variant, Product, Shop, Current, Reference, lows.c.low_cents, drop_pct.label("drop_pct"))
        .select_from(Variant)
        .join(Product, Variant.product_id == Product.id)
        .join(Shop, Variant.shop_id == Shop.id)
        .join(latest, latest.c.variant_id == Variant.id)
        .join(Current, and_(Current.variant_id == latest.c.variant_id, Current.captured_at == latest.c.captured_at))
        .join(reference, reference.c.variant_id == Variant.id)
        .join(
            Reference,
            and_(Reference.variant_id == reference.c.variant_id, Reference.captured_at == reference.c.captured_at),
        )
        .join(lows, lows.c.variant_id == Variant.id)
        .where(Reference.price_cents > 0)
        .where(drop_pct >= min_drop_pct)
    )
    if category:
        stmt = stmt.where(Product.category.in_(category))
    if in_stock_only:
        stmt = stmt.where(Current.in_stock.is_(True))

    total = session.scalar(select(func.count()).select_from(stmt.subquery()))

    rows = session.execute(
        stmt.order_by(drop_pct.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    results = []
    for variant, product, shop, current, reference_snapshot, low_cents, drop in rows:
        item = _to_result_item(variant, product, shop, current)
        results.append(
            DealItem(
                **item.model_dump(),
                reference_price_eur=reference_snapshot.price_cents / 100,
                reference_captured_at=reference_snapshot.captured_at,
                drop_eur=round((reference_snapshot.price_cents - current.price_cents) / 100, 2),
                drop_pct=round(float(drop), 1),
                is_all_time_low=current.price_cents <= low_cents,
                all_time_low_eur=low_cents / 100,
            )
        )

    return DealsResponse(total=total, page=page, page_size=page_size, window_days=window_days, results=results)


@router.get("/dashboard/shop-trust", response_model=ShopTrustResponse)
def shop_trust(session: Session = Depends(get_session)):
    """Per shop: of all currently advertised discounts, how many rest on a
    list price that was genuinely charged at some point in our history?"""
    aggregates = (
        select(
            PriceSnapshot.variant_id.label("variant_id"),
            func.max(PriceSnapshot.price_cents).label("max_charged_cents"),
            func.bool_or(PriceSnapshot.price_cents == PriceSnapshot.list_price_cents).label("list_ever_charged"),
        )
        .group_by(PriceSnapshot.variant_id)
        .subquery()
    )
    latest = _latest_price_subquery()
    Current = aliased(PriceSnapshot)

    # One row per variant; the per-snapshot scan stays in the database.
    rows = session.execute(
        select(
            Shop.name,
            Current.price_cents,
            Current.list_price_cents,
            aggregates.c.max_charged_cents,
            aggregates.c.list_ever_charged,
        )
        .select_from(Variant)
        .join(Shop, Variant.shop_id == Shop.id)
        .join(latest, latest.c.variant_id == Variant.id)
        .join(Current, and_(Current.variant_id == latest.c.variant_id, Current.captured_at == latest.c.captured_at))
        .join(aggregates, aggregates.c.variant_id == Variant.id)
    ).all()

    per_shop: dict[str, dict] = {}
    for shop_name, price_cents, list_price_cents, max_charged_cents, list_ever_charged in rows:
        bucket = per_shop.setdefault(
            shop_name, {"total": 0, "claimed": 0, "never_charged": 0, "claimed_pcts": [], "real_pcts": []}
        )
        bucket["total"] += 1
        if list_price_cents <= price_cents:
            continue  # no discount advertised right now

        bucket["claimed"] += 1
        if not list_ever_charged:
            bucket["never_charged"] += 1
        bucket["claimed_pcts"].append((list_price_cents - price_cents) / list_price_cents * 100)
        if max_charged_cents > price_cents:
            bucket["real_pcts"].append((max_charged_cents - price_cents) / max_charged_cents * 100)
        else:
            bucket["real_pcts"].append(0.0)

    def mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    shops = [
        ShopTrust(
            shop_name=name,
            variants_total=bucket["total"],
            variants_with_claimed_discount=bucket["claimed"],
            claimed_discount_never_charged=bucket["never_charged"],
            trust_pct=(
                round((bucket["claimed"] - bucket["never_charged"]) / bucket["claimed"] * 100, 1)
                if bucket["claimed"]
                else None
            ),
            avg_claimed_discount_pct=mean(bucket["claimed_pcts"]),
            avg_real_discount_pct=mean(bucket["real_pcts"]),
        )
        for name, bucket in per_shop.items()
    ]
    # Worst offenders first; shops without any advertised discount last.
    shops.sort(key=lambda s: (s.trust_pct is None, s.trust_pct if s.trust_pct is not None else 0))
    return ShopTrustResponse(shops=shops)
