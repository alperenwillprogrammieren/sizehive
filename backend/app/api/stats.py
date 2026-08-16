"""Per-article statistics (detail view) and the internal dashboard."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import (
    AttributePrices,
    AttributePricesResponse,
    AttributeValuePrice,
    CategoryCoverage,
    DashboardResponse,
    PriceDistributionGroup,
    PriceDistributionResponse,
    PricePoint,
    PriceStatsResponse,
    SimilarItem,
    SimilarResponse,
    VariantDetailResponse,
)
from app.api.search import (
    NON_SCALAR_ATTRS,
    _add_common_joins,
    _latest_price_subquery,
    _to_result_item,
    get_session,
)
from app.extract.report import coverage_report
from app.models import PriceSnapshot, Product, Shop, Variant
from app.pricing.history import Snapshot, price_stats
from app.recommend import similarity

router = APIRouter()


@router.get("/variants/{variant_id}", response_model=VariantDetailResponse)
def variant_detail(variant_id: int, session: Session = Depends(get_session)):
    row = session.execute(
        select(Variant, Product, Shop)
        .join(Product, Variant.product_id == Product.id)
        .join(Shop, Variant.shop_id == Shop.id)
        .where(Variant.id == variant_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="variant not found")
    variant, product, shop = row

    history = list(
        session.scalars(
            select(PriceSnapshot)
            .where(PriceSnapshot.variant_id == variant_id)
            .order_by(PriceSnapshot.captured_at.asc())
        )
    )
    current = history[-1]

    # Percentile score: current price vs. the latest price of every variant
    # in the same category ("comparable" = same category — jeans vs. jeans,
    # T-Shirt vs. T-Shirt, not jeans vs. sneakers).
    latest = _latest_price_subquery()
    comparable_prices = session.scalars(
        select(PriceSnapshot.price_cents)
        .select_from(Variant)
        .join(Product, Variant.product_id == Product.id)
        .join(latest, latest.c.variant_id == Variant.id)
        .join(
            PriceSnapshot,
            (PriceSnapshot.variant_id == latest.c.variant_id) & (PriceSnapshot.captured_at == latest.c.captured_at),
        )
        .where(Product.category == product.category)
    ).all()
    n_comparable = len(comparable_prices)
    n_pricier = sum(1 for p in comparable_prices if p > current.price_cents)
    percentile_score = round(n_pricier / n_comparable * 100, 1) if n_comparable else None

    stats = price_stats(
        [
            Snapshot(captured_at=s.captured_at, price_cents=s.price_cents, list_price_cents=s.list_price_cents)
            for s in history
        ]
    )

    return VariantDetailResponse(
        variant_id=variant.id,
        category=product.category,
        brand=product.brand,
        model_name=product.model_name,
        description=product.description,
        attributes=product.attributes,
        attribute_sources=product.attribute_sources,
        size_raw=variant.size_raw,
        size_w=variant.size_w,
        size_l=variant.size_l,
        color=variant.color,
        shop_name=shop.name,
        url=variant.url,
        image_url=variant.image_url,
        current_price_eur=current.price_cents / 100,
        current_list_price_eur=current.list_price_cents / 100,
        in_stock=current.in_stock,
        percentile_score=percentile_score,
        comparable_count=n_comparable,
        list_price_ever_charged=stats.list_price_ever_charged,
        price_stats=PriceStatsResponse(
            all_time_low_eur=stats.all_time_low_cents / 100,
            all_time_high_eur=stats.all_time_high_cents / 100,
            low_30d_eur=stats.low_30d_cents / 100 if stats.low_30d_cents is not None else None,
            low_90d_eur=stats.low_90d_cents / 100 if stats.low_90d_cents is not None else None,
            median_90d_eur=stats.median_90d_cents / 100 if stats.median_90d_cents is not None else None,
            is_all_time_low=stats.is_all_time_low,
            days_since_cheaper=stats.days_since_cheaper,
            claimed_discount_pct=stats.claimed_discount_pct,
            real_discount_pct=stats.real_discount_pct,
            first_seen=stats.first_seen,
            snapshot_count=stats.snapshot_count,
        ),
        price_history=[
            PricePoint(
                captured_at=s.captured_at,
                price_eur=s.price_cents / 100,
                list_price_eur=s.list_price_cents / 100,
                in_stock=s.in_stock,
            )
            for s in history
        ],
    )


#: Upper bound on candidates scored in Python. They are pre-selected in SQL
#: by price proximity, so the cap trims the tail, not the best matches.
SIMILAR_CANDIDATE_LIMIT = 400


@router.get("/variants/{variant_id}/similar", response_model=SimilarResponse)
def similar_variants(
    variant_id: int,
    limit: int = Query(6, ge=1, le=24),
    session: Session = Depends(get_session),
):
    """Articles described like this one — attribute overlap first, price second.

    Restricted to the same category because attribute vocabularies don't
    overlap across categories (a T-Shirt has no `wash`), and to other
    products so the list doesn't fill up with the same article at a
    different size.
    """
    row = session.execute(
        select(Variant, Product).join(Product, Variant.product_id == Product.id).where(Variant.id == variant_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="variant not found")
    base_variant, base_product = row

    latest = _latest_price_subquery()
    base_price = session.scalar(
        select(PriceSnapshot.price_cents)
        .join(latest, latest.c.variant_id == PriceSnapshot.variant_id)
        .where(PriceSnapshot.variant_id == variant_id, PriceSnapshot.captured_at == latest.c.captured_at)
    )
    if base_price is None:
        return SimilarResponse(results=[])

    candidates = session.execute(
        _add_common_joins(select(Variant, Product, Shop, PriceSnapshot))
        .where(Product.category == base_product.category)
        .where(Product.id != base_product.id)
        .where(PriceSnapshot.in_stock.is_(True))
        .order_by(func.abs(PriceSnapshot.price_cents - base_price))
        .limit(SIMILAR_CANDIDATE_LIMIT)
    ).all()

    scored = []
    for variant, product, shop, price in candidates:
        result = similarity(base_product.attributes, base_price, product.attributes, price.price_cents)
        scored.append((result, variant, product, shop, price))

    # Highest score first; the cheaper article wins an exact tie.
    scored.sort(key=lambda entry: (-entry[0].score, entry[4].price_cents))

    results = []
    seen_products: set[int] = set()
    for result, variant, product, shop, price in scored:
        if product.id in seen_products:
            continue  # one offer per product, not five sizes of the same jeans
        seen_products.add(product.id)
        item = _to_result_item(variant, product, shop, price)
        results.append(
            SimilarItem(**item.model_dump(), similarity=result.score, shared_attributes=result.shared_attributes)
        )
        if len(results) == limit:
            break

    return SimilarResponse(results=results)


PRICE_DIMENSIONS = {"brand": Product.brand, "category": Product.category}

#: Groups below this are dropped from the distributions — a "median" over
#: three articles is noise presented as a statistic.
MIN_GROUP_SIZE = 5


def _percentile(fraction: float, column):
    return func.percentile_cont(fraction).within_group(column.asc())


@router.get("/dashboard/price-distribution", response_model=PriceDistributionResponse)
def price_distribution(
    dimension: str = Query("category", description="brand | category"),
    session: Session = Depends(get_session),
):
    """Five-number summary of current prices per brand or category."""
    if dimension not in PRICE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="dimension must be 'brand' or 'category'")
    column = PRICE_DIMENSIONS[dimension]

    price = PriceSnapshot.price_cents
    rows = session.execute(
        _add_common_joins(
            select(
                column.label("group"),
                func.count().label("count"),
                func.min(price).label("min"),
                _percentile(0.25, price).label("p25"),
                _percentile(0.5, price).label("median"),
                _percentile(0.75, price).label("p75"),
                func.max(price).label("max"),
            )
        )
        .group_by(column)
        .having(func.count() >= MIN_GROUP_SIZE)
        .order_by(_percentile(0.5, price).desc())
    ).all()

    return PriceDistributionResponse(
        dimension=dimension,
        groups=[
            PriceDistributionGroup(
                group=group,
                count=count,
                min_eur=minimum / 100,
                p25_eur=p25 / 100,
                median_eur=median / 100,
                p75_eur=p75 / 100,
                max_eur=maximum / 100,
            )
            for group, count, minimum, p25, median, p75, maximum in rows
        ],
    )


@router.get("/dashboard/attribute-prices", response_model=AttributePricesResponse)
def attribute_prices(
    category: str = Query(..., description="e.g. Herrenjeans"),
    session: Session = Depends(get_session),
):
    """What does each attribute value cost, relative to its category?

    Answers questions like "do slim jeans really sell dearer than straight?"
    Attribute keys are discovered per category the same way the facets do it,
    so a new category needs no change here.
    """
    keys = sorted(
        {
            row[0]
            for row in session.execute(
                select(func.jsonb_object_keys(Product.attributes))
                .where(Product.category == category)
                .distinct()
            ).all()
        }
        - NON_SCALAR_ATTRS
    )

    price = PriceSnapshot.price_cents
    category_median = session.scalar(
        _add_common_joins(select(_percentile(0.5, price))).where(Product.category == category)
    )
    if category_median is None:
        return AttributePricesResponse(category=category, attributes=[])

    attributes = []
    for key in keys:
        column = Product.attributes[key].astext
        rows = session.execute(
            _add_common_joins(
                select(column.label("value"), func.count().label("count"), _percentile(0.5, price).label("median"))
            )
            .where(Product.category == category, column.isnot(None))
            .group_by(column)
            .having(func.count() >= MIN_GROUP_SIZE)
            .order_by(_percentile(0.5, price).desc())
        ).all()
        if len(rows) < 2:
            continue  # a single value has nothing to compare against

        # Baseline is the median across this attribute's own rows, not the
        # category median: values are unevenly distributed, and comparing
        # against the category would fold in articles that lack the attribute.
        medians = sorted(median for _, _, median in rows)
        middle = len(medians) // 2
        baseline = (
            medians[middle] if len(medians) % 2 else (medians[middle - 1] + medians[middle]) / 2
        )

        attributes.append(
            AttributePrices(
                attribute=key,
                median_eur=baseline / 100,
                values=[
                    AttributeValuePrice(
                        value=value,
                        count=count,
                        median_eur=median / 100,
                        delta_pct=round((median - baseline) / baseline * 100, 1) if baseline else 0.0,
                    )
                    for value, count, median in rows
                ],
            )
        )

    return AttributePricesResponse(category=category, attributes=attributes)


@router.get("/dashboard/coverage", response_model=DashboardResponse)
def dashboard_coverage(session: Session = Depends(get_session)):
    products = list(session.scalars(select(Product)))
    report = coverage_report(products)
    by_category = [
        CategoryCoverage(
            category=category,
            total_products=sum(1 for p in products if p.category == category),
            coverage=coverage,
        )
        for category, coverage in report.items()
    ]
    return DashboardResponse(total_products=len(products), by_category=by_category)
