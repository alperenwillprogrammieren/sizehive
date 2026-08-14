from datetime import datetime

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    variant_id: int
    product_id: int
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


class VariantDetailResponse(BaseModel):
    variant_id: int
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
    price_history: list[PricePoint]


class DashboardResponse(BaseModel):
    total_products: int
    coverage: dict[str, float]
    products_with_fit_and_wash: int
    products_with_fit_and_wash_pct: float
