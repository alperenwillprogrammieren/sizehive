"""Faceted search over the current product/variant/price catalog.

GET /api/search accepts any combination of the filters below plus sort and
pagination. GET /api/facets computes, for each facet attribute, the
available values and hit counts under the *other* currently active filters
(that attribute's own filter is excluded from its own count) — so the
frontend never has to show a filter option that would return zero results.
"""
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, and_, cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.api.schemas import FacetsResponse, FacetValue, SearchResponse, SearchResultItem
from app.db.session import SessionLocal
from app.models import PriceSnapshot, Product, Shop, Variant

router = APIRouter()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


SORT_OPTIONS = {"price_asc", "price_desc", "discount_desc", "newest"}


@dataclass
class SearchFilters:
    category: str = "Herrenjeans"
    gender: str | None = None
    brand: list[str] | None = None
    color: list[str] | None = None
    size_w: int | None = None
    size_l: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    in_stock_only: bool = False
    fit: str | None = None
    rise: str | None = None
    leg_shape: str | None = None
    wash: str | None = None
    closure: str | None = None
    stretch: bool | None = None
    sustainability: str | None = None
    cotton_min: int | None = None


def search_filters(
    category: str = Query("Herrenjeans"),
    gender: str | None = Query(None),
    brand: list[str] | None = Query(None, description="Repeat for multiple brands"),
    color: list[str] | None = Query(None, description="Canonical color slug, e.g. dark_blue"),
    size_w: int | None = Query(None),
    size_l: int | None = Query(None),
    price_min: float | None = Query(None, ge=0, description="EUR"),
    price_max: float | None = Query(None, ge=0, description="EUR"),
    in_stock_only: bool = Query(False),
    fit: str | None = Query(None),
    rise: str | None = Query(None),
    leg_shape: str | None = Query(None),
    wash: str | None = Query(None),
    closure: str | None = Query(None),
    stretch: bool | None = Query(None),
    sustainability: str | None = Query(None, description="e.g. gots, organic_cotton"),
    cotton_min: int | None = Query(None, ge=0, le=100, description="minimum cotton share, percent"),
) -> SearchFilters:
    return SearchFilters(
        category=category, gender=gender, brand=brand, color=color, size_w=size_w, size_l=size_l,
        price_min=price_min, price_max=price_max, in_stock_only=in_stock_only,
        fit=fit, rise=rise, leg_shape=leg_shape, wash=wash, closure=closure,
        stretch=stretch, sustainability=sustainability, cotton_min=cotton_min,
    )


def _latest_price_subquery():
    return (
        select(PriceSnapshot.variant_id, func.max(PriceSnapshot.captured_at).label("captured_at"))
        .group_by(PriceSnapshot.variant_id)
        .subquery()
    )


def _add_common_joins(stmt):
    latest = _latest_price_subquery()
    return (
        stmt.select_from(Variant)
        .join(Product, Variant.product_id == Product.id)
        .join(Shop, Variant.shop_id == Shop.id)
        .join(latest, latest.c.variant_id == Variant.id)
        .join(
            PriceSnapshot,
            and_(PriceSnapshot.variant_id == latest.c.variant_id, PriceSnapshot.captured_at == latest.c.captured_at),
        )
    )


def _apply_filters(stmt, filters: SearchFilters, exclude: str | None = None):
    conditions = [Product.category == filters.category]
    if filters.gender:
        conditions.append(Product.gender == filters.gender)
    if filters.brand and exclude != "brand":
        conditions.append(Product.brand.in_(filters.brand))
    if filters.color and exclude != "color":
        conditions.append(Variant.color.in_(filters.color))
    if filters.size_w is not None and exclude != "size_w":
        conditions.append(Variant.size_w == filters.size_w)
    if filters.size_l is not None and exclude != "size_l":
        conditions.append(Variant.size_l == filters.size_l)
    if filters.price_min is not None:
        conditions.append(PriceSnapshot.price_cents >= round(filters.price_min * 100))
    if filters.price_max is not None:
        conditions.append(PriceSnapshot.price_cents <= round(filters.price_max * 100))
    if filters.in_stock_only:
        conditions.append(PriceSnapshot.in_stock.is_(True))
    if filters.fit and exclude != "fit":
        conditions.append(Product.attributes["fit"].astext == filters.fit)
    if filters.rise and exclude != "rise":
        conditions.append(Product.attributes["rise"].astext == filters.rise)
    if filters.leg_shape and exclude != "leg_shape":
        conditions.append(Product.attributes["leg_shape"].astext == filters.leg_shape)
    if filters.wash and exclude != "wash":
        conditions.append(Product.attributes["wash"].astext == filters.wash)
    if filters.closure and exclude != "closure":
        conditions.append(Product.attributes["closure"].astext == filters.closure)
    if filters.stretch is not None:
        conditions.append(Product.attributes["stretch"].astext == ("true" if filters.stretch else "false"))
    if filters.sustainability:
        conditions.append(Product.attributes["sustainability"].op("@>")(cast([filters.sustainability], JSONB)))
    if filters.cotton_min is not None:
        conditions.append(cast(Product.attributes["material"]["cotton_pct"].astext, Integer) >= filters.cotton_min)
    return stmt.where(and_(*conditions))


def _apply_sort(stmt, sort: str):
    if sort == "price_asc":
        return stmt.order_by(PriceSnapshot.price_cents.asc())
    if sort == "price_desc":
        return stmt.order_by(PriceSnapshot.price_cents.desc())
    if sort == "discount_desc":
        return stmt.order_by((PriceSnapshot.list_price_cents - PriceSnapshot.price_cents).desc())
    return stmt.order_by(Variant.created_at.desc())  # newest


@router.get("/search", response_model=SearchResponse)
def search(
    filters: SearchFilters = Depends(search_filters),
    sort: str = Query("newest", description="price_asc | price_desc | discount_desc | newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    if sort not in SORT_OPTIONS:
        sort = "newest"

    base_stmt = _apply_filters(_add_common_joins(select(Variant, Product, Shop, PriceSnapshot)), filters)
    total = session.scalar(select(func.count()).select_from(base_stmt.subquery()))

    stmt = _apply_sort(base_stmt, sort).offset((page - 1) * page_size).limit(page_size)
    results = []
    for variant, product, shop, price in session.execute(stmt).all():
        list_price = price.list_price_cents
        discount_pct = ((list_price - price.price_cents) / list_price * 100) if list_price else 0.0
        results.append(
            SearchResultItem(
                variant_id=variant.id,
                product_id=product.id,
                brand=product.brand,
                model_name=product.model_name,
                attributes=product.attributes,
                size_w=variant.size_w,
                size_l=variant.size_l,
                size_raw=variant.size_raw,
                color=variant.color,
                shop_name=shop.name,
                price_eur=price.price_cents / 100,
                list_price_eur=price.list_price_cents / 100,
                discount_pct=round(discount_pct, 1),
                in_stock=price.in_stock,
                image_url=variant.image_url,
                url=variant.url,
            )
        )
    return SearchResponse(total=total, page=page, page_size=page_size, results=results)


# Multi-valued attributes (e.g. sustainability, a tag list) would need
# jsonb_array_elements to facet properly and are left out of MVP facets.
FACET_COLUMNS = {
    "brand": Product.brand,
    "color": Variant.color,
    "fit": Product.attributes["fit"].astext,
    "rise": Product.attributes["rise"].astext,
    "leg_shape": Product.attributes["leg_shape"].astext,
    "wash": Product.attributes["wash"].astext,
    "closure": Product.attributes["closure"].astext,
}


@router.get("/facets", response_model=FacetsResponse)
def facets(filters: SearchFilters = Depends(search_filters), session: Session = Depends(get_session)):
    result: dict[str, list[FacetValue]] = {}
    for name, column in FACET_COLUMNS.items():
        stmt = select(column.label("value"), func.count(func.distinct(Variant.id)).label("count"))
        stmt = _add_common_joins(stmt)
        stmt = _apply_filters(stmt, filters, exclude=name)
        stmt = stmt.where(column.isnot(None)).group_by(column).order_by(func.count(func.distinct(Variant.id)).desc())
        result[name] = [FacetValue(value=value, count=count) for value, count in session.execute(stmt).all()]
    return FacetsResponse(facets=result)
