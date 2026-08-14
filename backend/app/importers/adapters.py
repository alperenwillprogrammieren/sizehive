"""Per-feed adapters: raw file -> normalized row dicts.

Each adapter hides that feed's specific schema/dialect (column names,
delimiter, decimal separator, availability vocabulary, XML vs CSV) and
yields dicts with a shared shape, so `importer.import_row` never needs to
know which shop a row came from.
"""
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

from app.importers.common import derive_model_name, parse_price_cents

CATEGORY = "Herrenjeans"
GENDER = "male"


def parse_awin_csv(path: Path) -> Iterator[dict]:
    availability_in_stock = {"in stock", "preorder"}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            yield {
                "shop_sku": row["sku"],
                "ean": row["ean"] or None,
                "brand": row["brand"],
                "model_name": derive_model_name(row["product_name"], row["brand"]),
                "description": row["description"],
                "category": CATEGORY,
                "gender": GENDER,
                "size_raw": row["size"],
                "color": row["color"],
                "price_cents": parse_price_cents(row["price"]),
                "list_price_cents": parse_price_cents(row["list_price"]),
                "in_stock": row["availability"] in availability_in_stock,
                "image_url": row["image_url"],
                "deeplink_url": row["deeplink_url"],
            }


def parse_belboon_csv(path: Path) -> Iterator[dict]:
    availability_in_stock = {"verfuegbar", "auf Lager"}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            yield {
                "shop_sku": row["ARTIKELNR"],
                "ean": row["EAN_CODE"] or None,
                "brand": row["MARKE"],
                "model_name": derive_model_name(row["TITEL"], row["MARKE"]),
                "description": row["BESCHREIBUNG"],
                "category": CATEGORY,
                "gender": GENDER,
                "size_raw": row["GROESSE"],
                "color": row["FARBE"],
                "price_cents": parse_price_cents(row["PREIS_EUR"], decimal_sep=","),
                "list_price_cents": parse_price_cents(row["STREICHPREIS_EUR"], decimal_sep=","),
                "in_stock": row["LAGERSTATUS"] in availability_in_stock,
                "image_url": row["BILD"],
                "deeplink_url": row["LINK"],
            }


def parse_tradedoubler_xml(path: Path) -> Iterator[dict]:
    root = ET.parse(path).getroot()
    for p in root.findall("product"):
        text = lambda tag: (p.findtext(tag) or "").strip()
        yield {
            "shop_sku": text("sku"),
            "ean": text("ean") or None,
            "brand": text("brand"),
            "model_name": derive_model_name(text("title"), text("brand")),
            "description": text("description"),
            "category": CATEGORY,
            "gender": GENDER,
            "size_raw": text("size"),
            "color": text("colour"),
            "price_cents": parse_price_cents(text("price")),
            "list_price_cents": parse_price_cents(text("rrp")),
            "in_stock": text("in_stock") == "1",
            "image_url": text("image"),
            "deeplink_url": text("url"),
        }
