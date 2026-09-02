"""Faceted search over the current product/variant/price catalog.

GET /api/search accepts any combination of the filters below plus sort and
pagination. GET /api/facets computes, for each facet attribute, the
available values and hit counts under the *other* currently active filters
(that attribute's own filter is excluded from its own count) — so the
frontend never has to show a filter option that would return zero results.

Kür (derived) attributes are filtered generically: any query parameter that
isn't one of the reserved names below is treated as an equality filter on
Product.attributes[<param name>] — e.g. `?fit=slim` or `?sleeve=short` or
`?upper_material=leather`. This is what lets a new category (see
app.taxonomy) add filterable attributes without touching this endpoint.
"""
from dataclasses import dataclass, field
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import Integer, and_, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.api.schemas import (
    FacetsResponse,
    FacetValue,
    SearchResponse,
    SearchResultItem,
    Suggestion,
    SuggestResponse,
    VariantBatchResponse,
)
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

# Query params with dedicated, non-generic handling (structural filters, or
# attributes whose comparison isn't flat equality). Everything else in the
# querystring is treated as a generic Kür-attribute equality filter.
RESERVED_PARAMS = {
    "category", "gender", "brand", "color", "size_w", "size_l", "price_min", "price_max",
    "in_stock_only", "q", "cotton_min", "sustainability", "sort", "page", "page_size",
}

# JSONB attribute keys that aren't a flat scalar (material is a nested
# object, sustainability is a tag list) — excluded from the generic
# equality mechanism and from dynamic facet discovery; each has its own
# comparison semantics (see cotton_min / sustainability below).
NON_SCALAR_ATTRS = {"material", "sustainability"}


# Typo tolerance is a *fallback*: the strict substring match runs first, and
# only when it finds nothing does the query re-run against pg_trgm's
# word_similarity. That keeps the common case exact and fast, and makes a
# generous threshold the right call — the alternative to a fuzzy hit is an
# empty result page. Measured against the sample catalog: "tomy hilfiger"
# scores 0.81, "slimm taperd" 0.64, "levsi" 0.50, "wranlger" 0.44, while
# actual gibberish scores 0.00.
FUZZY_THRESHOLD = 0.4


@dataclass
class SearchFilters:
    category: list[str] | None = None
    gender: list[str] | None = None
    brand: list[str] | None = None
    color: list[str] | None = None
    size_w: int | None = None
    size_l: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    in_stock_only: bool = False
    q: str | None = None
    cotton_min: int | None = None
    sustainability: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    #: Set by the endpoint, not by the caller — see FUZZY_THRESHOLD.
    fuzzy: bool = False


def search_filters(
    request: Request,
    category: list[str] | None = Query(None, description="Repeat for multiple categories"),
    gender: list[str] | None = Query(None, description="male/female/unisex, repeat for multiple"),
    brand: list[str] | None = Query(None, description="Repeat for multiple brands"),
    color: list[str] | None = Query(None, description="Canonical color slug, e.g. dark_blue"),
    size_w: int | None = Query(None),
    size_l: int | None = Query(None),
    price_min: float | None = Query(None, ge=0, description="EUR"),
    price_max: float | None = Query(None, ge=0, description="EUR"),
    in_stock_only: bool = Query(False),
    q: str | None = Query(None, description="Volltextsuche über Marke, Modell, Beschreibung"),
    cotton_min: int | None = Query(None, ge=0, le=100, description="minimum cotton share, percent"),
    sustainability: str | None = Query(None, description="e.g. gots, organic_cotton"),
) -> SearchFilters:
    attrs = {key: request.query_params[key] for key in request.query_params.keys() if key not in RESERVED_PARAMS}
    return SearchFilters(
        category=category, gender=gender, brand=brand, color=color, size_w=size_w, size_l=size_l,
        price_min=price_min, price_max=price_max, in_stock_only=in_stock_only, q=q,
        cotton_min=cotton_min, sustainability=sustainability, attrs=attrs,
    )


def _coerce(value: str | None, cast):
    """Stored agent queries are just strings and may be stale or malformed;
    an unparseable value drops the filter instead of failing the run."""
    if value is None:
        return None
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def filters_from_query_string(query: str) -> SearchFilters:
    """Build SearchFilters from a raw querystring, with no HTTP request.

    Search agents (app/notify/run.py) store exactly the querystring the
    frontend puts in the URL, so they need the same parsing the endpoint
    does — without going through FastAPI's dependency machinery.
    """
    raw = parse_qs(query.lstrip("?"), keep_blank_values=False)

    def first(key: str) -> str | None:
        values = raw.get(key)
        return values[0] if values else None

    return SearchFilters(
        category=raw.get("category"),
        gender=raw.get("gender"),
        brand=raw.get("brand"),
        color=raw.get("color"),
        size_w=_coerce(first("size_w"), int),
        size_l=_coerce(first("size_l"), int),
        price_min=_coerce(first("price_min"), float),
        price_max=_coerce(first("price_max"), float),
        in_stock_only=first("in_stock_only") == "true",
        q=first("q"),
        cotton_min=_coerce(first("cotton_min"), int),
        sustainability=first("sustainability"),
        attrs={key: values[0] for key, values in raw.items() if key not in RESERVED_PARAMS and values},
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
    conditions = []
    if filters.category and exclude != "category":
        conditions.append(Product.category.in_(filters.category))
    if filters.gender and exclude != "gender":
        conditions.append(Product.gender.in_(filters.gender))
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
    if filters.q:
        if filters.fuzzy:
            conditions.append(
                func.word_similarity(filters.q, Product.brand + " " + Product.model_name) >= FUZZY_THRESHOLD
            )
        else:
            pattern = f"%{filters.q}%"
            conditions.append(
                or_(
                    Product.brand.ilike(pattern),
                    Product.model_name.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )
    if filters.sustainability:
        conditions.append(Product.attributes["sustainability"].op("@>")(cast([filters.sustainability], JSONB)))
    if filters.cotton_min is not None:
        conditions.append(cast(Product.attributes["material"]["cotton_pct"].astext, Integer) >= filters.cotton_min)
    for key, value in filters.attrs.items():
        if key == exclude:
            continue
        conditions.append(Product.attributes[key].astext == value)
    return stmt.where(and_(*conditions)) if conditions else stmt


def _to_result_item(variant: Variant, product: Product, shop: Shop, price: PriceSnapshot) -> SearchResultItem:
    list_price = price.list_price_cents
    discount_pct = ((list_price - price.price_cents) / list_price * 100) if list_price else 0.0
    return SearchResultItem(
        variant_id=variant.id,
        product_id=product.id,
        category=product.category,
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


def _apply_sort(stmt, sort: str):
    if sort == "price_asc":
        return stmt.order_by(PriceSnapshot.price_cents.asc())
    if sort == "price_desc":
        return stmt.order_by(PriceSnapshot.price_cents.desc())
    if sort == "discount_desc":
        return stmt.order_by((PriceSnapshot.list_price_cents - PriceSnapshot.price_cents).desc())
    return stmt.order_by(Variant.created_at.desc())  # newest


def resolve_fuzzy(session: Session, filters: SearchFilters) -> bool:
    """Decide whether this request should fall back to typo tolerance.

    Costs one extra count query, and only when a free-text term is present.
    Both /search and /facets call it so the sidebar can't end up describing
    a different result set than the one on screen.
    """
    if not filters.q:
        return False
    strict = _apply_filters(_add_common_joins(select(Variant.id)), filters)
    return session.scalar(select(func.count()).select_from(strict.subquery())) == 0


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

    filters.fuzzy = resolve_fuzzy(session, filters)

    base_stmt = _apply_filters(_add_common_joins(select(Variant, Product, Shop, PriceSnapshot)), filters)
    total = session.scalar(select(func.count()).select_from(base_stmt.subquery()))

    stmt = _apply_sort(base_stmt, sort).offset((page - 1) * page_size).limit(page_size)
    results = [_to_result_item(*row) for row in session.execute(stmt).all()]
    return SearchResponse(
        total=total, page=page, page_size=page_size, results=results, fuzzy=filters.fuzzy and total > 0
    )


SUGGEST_SOURCES = {"brand": Product.brand, "model": Product.model_name, "category": Product.category}


@router.get("/suggest", response_model=SuggestResponse)
def suggest(
    q: str = Query(..., min_length=2, description="Partial term from the search box"),
    limit: int = Query(8, ge=1, le=20),
    session: Session = Depends(get_session),
):
    """Autocomplete over brands, model names and categories.

    Substring match OR trigram similarity in one pass — unlike /search this
    has no fallback step, because a suggestion list that quietly stays empty
    on a typo is exactly the case autocomplete exists to fix.
    """
    pattern = f"%{q}%"
    suggestions: list[Suggestion] = []

    for kind, column in SUGGEST_SOURCES.items():
        stmt = (
            _add_common_joins(select(column.label("value"), func.count(func.distinct(Variant.id)).label("count")))
            .where(or_(column.ilike(pattern), func.word_similarity(q, column) >= FUZZY_THRESHOLD))
            .group_by(column)
            .order_by(func.count(func.distinct(Variant.id)).desc())
            .limit(limit)
        )
        suggestions.extend(
            Suggestion(value=value, kind=kind, count=count) for value, count in session.execute(stmt).all()
        )

    # Brands and categories are the more useful jump-off points, so they win
    # ties against a model name with the same hit count.
    rank = {"brand": 0, "category": 1, "model": 2}
    suggestions.sort(key=lambda s: (rank[s.kind], -s.count))
    return SuggestResponse(suggestions=suggestions[:limit])


MAX_BATCH_IDS = 200


@router.get("/variants", response_model=VariantBatchResponse)
def variants_batch(
    ids: str = Query("", description="Comma-separated variant ids, e.g. ?ids=12,44,91"),
    session: Session = Depends(get_session),
):
    """Current state of a known set of variants, in the same item shape as
    /api/search. Backs client-side collections (watchlist, recently viewed)
    that store nothing but ids locally and re-resolve prices on every view —
    so a saved entry can never show a stale price."""
    wanted = []
    for chunk in ids.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            wanted.append(int(chunk))
    wanted = list(dict.fromkeys(wanted))[:MAX_BATCH_IDS]
    if not wanted:
        return VariantBatchResponse(results=[])

    stmt = _add_common_joins(select(Variant, Product, Shop, PriceSnapshot)).where(Variant.id.in_(wanted))
    by_id = {row[0].id: _to_result_item(*row) for row in session.execute(stmt).all()}
    # Preserve the caller's order; silently skip ids that no longer exist.
    return VariantBatchResponse(results=[by_id[vid] for vid in wanted if vid in by_id])


FIXED_FACET_COLUMNS = {
    "category": Product.category,
    "gender": Product.gender,
    "brand": Product.brand,
    "color": Variant.color,
}


def _discover_attribute_keys(session: Session) -> list[str]:
    """Distinct JSONB attribute keys actually present across all products,
    minus the non-scalar ones. No per-category registration needed — a new
    category's extractor output shows up here automatically."""
    stmt = select(func.jsonb_object_keys(Product.attributes)).distinct()
    keys = {row[0] for row in session.execute(stmt).all()}
    return sorted(keys - NON_SCALAR_ATTRS)


@router.get("/facets", response_model=FacetsResponse)
def facets(filters: SearchFilters = Depends(search_filters), session: Session = Depends(get_session)):
    filters.fuzzy = resolve_fuzzy(session, filters)
    facet_columns = dict(FIXED_FACET_COLUMNS)
    for key in _discover_attribute_keys(session):
        facet_columns[key] = Product.attributes[key].astext

    result: dict[str, list[FacetValue]] = {}
    for name, column in facet_columns.items():
        stmt = select(column.label("value"), func.count(func.distinct(Variant.id)).label("count"))
        stmt = _add_common_joins(stmt)
        stmt = _apply_filters(stmt, filters, exclude=name)
        stmt = stmt.where(column.isnot(None)).group_by(column).order_by(func.count(func.distinct(Variant.id)).desc())
        result[name] = [FacetValue(value=value, count=count) for value, count in session.execute(stmt).all()]
    return FacetsResponse(facets=result)
