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
