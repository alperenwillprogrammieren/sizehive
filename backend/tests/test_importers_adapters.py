import csv

from app.importers.adapters import parse_awin_live_csv

FIELDS = [
    "merchant_product_id", "merchant_product_category_path", "brand_name",
    "product_name", "description", "colour", "search_price", "rrp_price",
    "in_stock", "Fashion:size", "product_GTIN", "aw_image_url",
    "merchant_image_url", "aw_deep_link",
]


def _write_feed(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _row(**overrides):
    row = {
        "merchant_product_id": "SKU-1",
        "merchant_product_category_path": "Herren > Hosen > Jeans",
        "brand_name": "Levi's",
        "product_name": "Levi's 501 Straight",
        "description": "Klassische Straight-Fit Jeans.",
        "colour": "Blue",
        "search_price": "89.90",
        "rrp_price": "99.90",
        "in_stock": "1",
        "Fashion:size": "W32L34",
        "product_GTIN": "4062678092905",
        "aw_image_url": "https://images2.productserve.com/example.jpg",
        "merchant_image_url": "https://uni-polar.de/media/example.jpg",
        "aw_deep_link": "https://www.awin1.com/pclick.php?p=1&a=3059091&m=106791",
    }
    row.update(overrides)
    return row


def test_maps_mens_jeans_category(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row()])

    rows = list(parse_awin_live_csv(path))

    assert len(rows) == 1
    row = rows[0]
    assert row["category"] == "Herrenjeans"
    assert row["gender"] == "male"
    assert row["shop_sku"] == "SKU-1"
    assert row["brand"] == "Levi's"
    assert row["price_cents"] == 8990
    assert row["list_price_cents"] == 9990
    assert row["in_stock"] is True
    assert row["ean"] == "4062678092905"
    assert row["deeplink_url"] == "https://www.awin1.com/pclick.php?p=1&a=3059091&m=106791"


def test_prefers_merchant_image_over_awin_thumbnail(tmp_path):
    """Awin's aw_image_url is a 200px-capped letterbox thumbnail; the shop's
    own image is full resolution, so that one wins when present."""
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row()])

    rows = list(parse_awin_live_csv(path))

    assert rows[0]["image_url"] == "https://uni-polar.de/media/example.jpg"


def test_falls_back_to_awin_image_when_merchant_image_missing(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(merchant_image_url="")])

    rows = list(parse_awin_live_csv(path))

    assert rows[0]["image_url"] == "https://images2.productserve.com/example.jpg"


def test_html_entities_in_feed_text_are_decoded(tmp_path):
    """The live feed ships HTML-escaped values ("full forest &amp; orange")
    that we render verbatim into colour names and titles."""
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(
        colour="full forest &amp; orange",
        product_name="Levi&#039;s &quot;501&quot; Straight",
        description="Jeans mit Knopf &amp; Reissverschluss",
    )])

    row = next(iter(parse_awin_live_csv(path)))

    assert row["color"] == "full forest & orange"
    assert row["description"] == "Jeans mit Knopf & Reissverschluss"
    assert "&quot;" not in row["model_name"] and "&#039;" not in row["model_name"]


def test_maps_womens_jeans_category(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(merchant_product_category_path="Damen > Hosen > Jeans")])

    rows = list(parse_awin_live_csv(path))

    assert len(rows) == 1
    assert rows[0]["category"] == "Damenjeans"
    assert rows[0]["gender"] == "female"


def test_skips_unmapped_category(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(merchant_product_category_path="Damen > Wäsche > Unterwäsche")])

    assert list(parse_awin_live_csv(path)) == []


def test_maps_tshirts_and_sneakers_for_both_genders(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [
        _row(merchant_product_id="T1", merchant_product_category_path="Herren > Bekleidung > T-Shirts > Basics"),
        _row(merchant_product_id="T2", merchant_product_category_path="Damen > Bekleidung > T-Shirts > Science"),
        _row(merchant_product_id="S1", merchant_product_category_path="Herren > Schuhe > Sneaker"),
        _row(merchant_product_id="S2", merchant_product_category_path="Damen > Schuhe > Sneaker"),
    ])

    rows = {row["shop_sku"]: row for row in parse_awin_live_csv(path)}

    assert rows["T1"]["category"] == "T-Shirts"
    assert rows["T2"]["category"] == "T-Shirts"
    assert rows["S1"]["category"] == "Sneaker"
    assert rows["S2"]["category"] == "Sneaker"
    assert all(row["gender"] == "unisex" for row in rows.values())


def test_out_of_stock_and_missing_gtin(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(in_stock="0", product_GTIN="")])

    row = next(parse_awin_live_csv(path))

    assert row["in_stock"] is False
    assert row["ean"] is None
