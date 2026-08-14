"""M7: per-article statistics (detail view) and an internal coverage dashboard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import DashboardResponse, PricePoint, VariantDetailResponse
from app.api.search import _latest_price_subquery, get_session
from app.extract.report import coverage_report
from app.models import PriceSnapshot, Product, Shop, Variant

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
    # in the same category ("comparable jeans" — MVP has only one category).
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

    list_price_ever_charged = any(s.price_cents == s.list_price_cents for s in history)

    return VariantDetailResponse(
        variant_id=variant.id,
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
        list_price_ever_charged=list_price_ever_charged,
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


@router.get("/dashboard/coverage", response_model=DashboardResponse)
def dashboard_coverage(session: Session = Depends(get_session)):
    products = list(session.scalars(select(Product)))
    coverage = coverage_report(products)
    both_fit_and_wash = sum(1 for p in products if "fit" in p.attributes and "wash" in p.attributes)
    return DashboardResponse(
        total_products=len(products),
        coverage=coverage,
        products_with_fit_and_wash=both_fit_and_wash,
        products_with_fit_and_wash_pct=round(both_fit_and_wash / len(products) * 100, 1) if products else 0.0,
    )
