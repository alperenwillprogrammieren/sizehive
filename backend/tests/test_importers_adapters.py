import csv

from app.importers.adapters import parse_awin_live_csv

FIELDS = [
    "merchant_product_id", "merchant_product_category_path", "brand_name",
    "product_name", "description", "colour", "search_price", "rrp_price",
    "in_stock", "Fashion:size", "product_GTIN", "aw_image_url", "aw_deep_link",
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


def test_skips_womens_jeans_out_of_scope(tmp_path):
    path = tmp_path / "awin.csv"
    _write_feed(path, [_row(merchant_product_category_path="Damen > Hosen > Jeans")])

    assert list(parse_awin_live_csv(path)) == []


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
