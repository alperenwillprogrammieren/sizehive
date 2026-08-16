from datetime import datetime

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    variant_id: int
    product_id: int
    category: str
    brand: str
    model_name: str
    attributes: dict
    size_w: int | None
    size_l: int | None
    size_raw: str
    color: str
    shop_name: str
    price_eur: float
    list_price_eur: float
    discount_pct: float
    in_stock: bool
    image_url: str
    url: str


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[SearchResultItem]


class VariantBatchResponse(BaseModel):
    results: list[SearchResultItem]


class FacetValue(BaseModel):
    value: str
    count: int


class FacetsResponse(BaseModel):
    facets: dict[str, list[FacetValue]]


class PricePoint(BaseModel):
    captured_at: datetime
    price_eur: float
    list_price_eur: float
    in_stock: bool


class PriceStatsResponse(BaseModel):
    """Measured price context for one variant — see app/pricing/history.py."""
    all_time_low_eur: float
    all_time_high_eur: float
    low_30d_eur: float | None
    low_90d_eur: float | None
    median_90d_eur: float | None
    is_all_time_low: bool
    days_since_cheaper: int | None
    #: What the shop advertises: list price vs. current price.
    claimed_discount_pct: float
    #: What we measured: highest price ever actually charged vs. current.
    real_discount_pct: float
    first_seen: datetime
    snapshot_count: int


class VariantDetailResponse(BaseModel):
    variant_id: int
    category: str
    brand: str
    model_name: str
    description: str
    attributes: dict
    attribute_sources: dict
    size_raw: str
    size_w: int | None
    size_l: int | None
    color: str
    shop_name: str
    url: str
    image_url: str
    current_price_eur: float
    current_list_price_eur: float
    in_stock: bool
    percentile_score: float | None
    comparable_count: int
    list_price_ever_charged: bool
    price_stats: PriceStatsResponse
    price_history: list[PricePoint]


class DealItem(SearchResultItem):
    """A search result plus the measured price drop that makes it a deal.
    `discount_pct` (inherited) is the shop's claim; `drop_pct` is observed."""
    reference_price_eur: float
    reference_captured_at: datetime
    drop_eur: float
    drop_pct: float
    is_all_time_low: bool
    all_time_low_eur: float


class DealsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    window_days: int
    results: list[DealItem]


class ShopTrust(BaseModel):
    shop_name: str
    variants_total: int
    variants_with_claimed_discount: int
    claimed_discount_never_charged: int
    #: Share of advertised discounts whose list price was genuinely charged
    #: at some point. None when the shop advertises no discounts at all.
    trust_pct: float | None
    avg_claimed_discount_pct: float | None
    avg_real_discount_pct: float | None


class ShopTrustResponse(BaseModel):
    shops: list[ShopTrust]


class CategoryCoverage(BaseModel):
    category: str
    total_products: int
    coverage: dict[str, float]


class DashboardResponse(BaseModel):
    total_products: int
    by_category: list[CategoryCoverage]
