"""Generate three realistically messy sample jeans feeds for local dev.

Simulates three affiliate feeds with different schemas/formats (two CSV
dialects with different column names, one XML), the way real affiliate
networks (Awin, Belboon, Tradedoubler) would actually differ. Deliberately
introduces the messiness M3/M4 need something real to work against: mixed
size notations, missing EANs, attributes only in free-text descriptions,
and inconsistent brand spellings.

Usage: python scripts/generate_sample_feeds.py
"""
import csv
import random
import xml.etree.ElementTree as ET
from pathlib import Path

random.seed(42)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

# Canonical brand -> spelling variants a messy feed might use.
BRANDS = {
    "Levi's": ["Levi's", "LEVIS", "Levi Strauss & Co."],
    "Wrangler": ["Wrangler", "WRANGLER"],
    "Lee": ["Lee", "LEE Jeans"],
    "Diesel": ["Diesel", "DIESEL"],
    "Tommy Hilfiger": ["Tommy Hilfiger", "Tommy Hilfiger Denim", "TOMMY HILFIGER"],
    "Calvin Klein": ["Calvin Klein", "Calvin Klein Jeans", "CK"],
    "G-Star": ["G-Star", "G-Star RAW", "G STAR"],
    "Pepe Jeans": ["Pepe Jeans", "PEPE JEANS LONDON"],
    "Jack & Jones": ["Jack & Jones", "JACK JONES", "Jack&Jones"],
    "Nudie Jeans": ["Nudie Jeans", "NUDIE"],
    "Replay": ["Replay", "REPLAY"],
    "BOSS": ["BOSS", "Hugo Boss"],
}

MODEL_SUFFIXES = [
    "501 Original", "511 Slim", "Skinny Fit", "Loose Tapered", "Regular Straight",
    "Baggy Wide Leg", "Athletic Tapered", "Relaxed Straight", "Slim Tapered",
    "Wide Leg High Rise", "Straight Fit", "Bootcut Classic",
]

FITS = ["skinny", "slim", "straight", "regular", "relaxed", "loose", "baggy", "wide leg"]
FIT_PHRASES = {
    "skinny": ["Skinny Fit", "super enge Passform", "skinny cut"],
    "slim": ["Slim Fit", "schmale Passform", "slim cut"],
    "straight": ["Straight Fit", "gerades Bein", "straight leg"],
    "regular": ["Regular Fit", "klassische Passform"],
    "relaxed": ["Relaxed Fit", "entspannte Passform"],
    "loose": ["Loose Fit", "lockere Passform", "weites Bein"],
    "baggy": ["Baggy Fit", "Baggy", "extra weit geschnitten"],
    "wide leg": ["Wide Leg", "weites Hosenbein", "ausgestelltes Bein"],
}
RISES = ["low", "mid", "high"]
RISE_PHRASES = {
    "low": ["Low Waist", "tief sitzend"],
    "mid": ["Mid Waist", "normale Bundhöhe"],
    "high": ["High Waist", "hohe Bundhöhe", "high rise"],
}
LEG_SHAPES = ["tapered", "straight", "bootcut", "flared"]
LEG_SHAPE_PHRASES = {
    "tapered": ["Tapered Leg", "verjüngtes Bein"],
    "straight": ["Straight Leg", "gerades Bein"],
    "bootcut": ["Bootcut", "leicht ausgestellt"],
    "flared": ["Flared", "Schlaghose"],
}
WASHES = ["raw", "light", "mid", "dark", "black", "stonewashed", "used", "destroyed"]
WASH_PHRASES = {
    "raw": ["Raw Denim", "ungewaschen"],
    "light": ["Light Wash", "hell gewaschen"],
    "mid": ["Mid Wash", "mittlere Waschung"],
    "dark": ["Dark Wash", "dunkel gewaschen"],
    "black": ["Black Denim", "schwarz"],
    "stonewashed": ["Stonewashed", "stone washed"],
    "used": ["Used Look", "used waschung"],
    "destroyed": ["Destroyed", "destroyed look", "mit Rissen"],
}
COLORS = ["dunkelblau", "hellblau", "schwarz", "grau", "indigo", "mittelblau", "khaki"]
MATERIALS = [
    ("100% Baumwolle", "Bio-Baumwolle" ), ("98% Baumwolle, 2% Elasthan", None),
    ("99% Cotton, 1% Elastane", None), ("100% Cotton", "GOTS zertifiziert"),
    ("80% Baumwolle, 18% Polyester, 2% Elasthan", None),
]
CLOSURES = ["Knopfleiste", "Reißverschluss"]

SIZE_FORMATS = [
    lambda w, l: f"W{w}/L{l}",
    lambda w, l: f"{w}/{l}",
    lambda w, l: f"W {w} L {l}",
    lambda w, l: f"{w}x{l}",
]
WIDTHS = [28, 29, 30, 31, 32, 33, 34, 36, 38]
LENGTHS = [30, 32, 34, 36]

# A pool of ~50 distinct "products"; multiple shops may sell the same one
# under a differently spelled brand name, and each is sold in several sizes.
CANON_BRANDS = list(BRANDS.keys())
PRODUCT_TEMPLATES = []
for _ in range(50):
    brand = random.choice(CANON_BRANDS)
    model = random.choice(MODEL_SUFFIXES)
    fit = random.choice(FITS)
    rise = random.choice(RISES)
    leg_shape = random.choice(LEG_SHAPES)
    wash = random.choice(WASHES)
    material, sustainability = random.choice(MATERIALS)
    closure = random.choice(CLOSURES)
    PRODUCT_TEMPLATES.append(
        dict(
            brand=brand, model=model, fit=fit, rise=rise, leg_shape=leg_shape,
            wash=wash, material=material, sustainability=sustainability, closure=closure,
        )
    )


def build_description(tpl: dict) -> str:
    parts = [
        f"{tpl['brand']} {tpl['model']}.",
        f"{random.choice(FIT_PHRASES[tpl['fit']])}, {random.choice(RISE_PHRASES[tpl['rise']])}.",
        f"{random.choice(LEG_SHAPE_PHRASES[tpl['leg_shape']])}, {random.choice(WASH_PHRASES[tpl['wash']])}.",
        f"Material: {tpl['material']}.",
        f"Verschluss: {tpl['closure']}.",
    ]
    if tpl["sustainability"]:
        parts.append(f"{tpl['sustainability']}.")
    if random.random() < 0.5:
        parts.append("Stretchanteil für hohen Tragekomfort.")
    return " ".join(parts)


def maybe_missing_ean() -> str:
    return "" if random.random() < 0.2 else str(random.randint(4_000_000_000_000, 4_999_999_999_999))


def random_size_raw() -> tuple[str, int, int]:
    w, l = random.choice(WIDTHS), random.choice(LENGTHS)
    fmt = random.choice(SIZE_FORMATS)
    return fmt(w, l), w, l


def price_pair() -> tuple[int, int]:
    list_price = random.randint(3990, 14990)
    discount = random.random()
    if discount < 0.4:
        price = list_price  # never discounted -> useful for the M7 discount-honesty check
    else:
        price = int(list_price * random.uniform(0.5, 0.95))
    return price, list_price


def spelled_brand(canon_brand: str) -> str:
    return random.choice(BRANDS[canon_brand])


def gen_rows(n: int, shop_variant_bias: int):
    """Yield n raw rows sampled from PRODUCT_TEMPLATES with per-shop brand spelling."""
    for i in range(n):
        tpl = PRODUCT_TEMPLATES[(i + shop_variant_bias) % len(PRODUCT_TEMPLATES)]
        size_raw, w, l = random_size_raw()
        price, list_price = price_pair()
        yield {
            "sku": f"S{shop_variant_bias}-{i:05d}",
            "ean": maybe_missing_ean(),
            "brand": spelled_brand(tpl["brand"]),
            "model": tpl["model"],
            "description": build_description(tpl),
            "size_raw": size_raw,
            "color": random.choice(COLORS),
            "price_cents": price,
            "list_price_cents": list_price,
            "image_url": f"https://picsum.photos/seed/{shop_variant_bias}-{i}/400/500",
        }


def write_awin_csv(path: Path, n: int = 220):
    rows = list(gen_rows(n, shop_variant_bias=0))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sku", "ean", "brand", "product_name", "description", "category",
            "size", "color", "price", "list_price", "availability", "image_url", "deeplink_url",
        ])
        availability_choices = ["in stock", "out of stock", "preorder"]
        for r in rows:
            writer.writerow([
                r["sku"], r["ean"], r["brand"], f"{r['brand']} {r['model']}", r["description"],
                "Herrenjeans", r["size_raw"], r["color"],
                f"{r['price_cents'] / 100:.2f}", f"{r['list_price_cents'] / 100:.2f}",
                random.choices(availability_choices, weights=[85, 10, 5])[0],
                r["image_url"], f"https://awin-tracking.example.com/click?sku={r['sku']}",
            ])


def write_belboon_csv(path: Path, n: int = 230):
    rows = list(gen_rows(n, shop_variant_bias=17))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ARTIKELNR", "EAN_CODE", "MARKE", "TITEL", "BESCHREIBUNG", "WARENGRUPPE",
            "GROESSE", "FARBE", "PREIS_EUR", "STREICHPREIS_EUR", "LAGERSTATUS", "BILD", "LINK",
        ])
        availability_choices = ["verfuegbar", "ausverkauft", "auf Lager"]
        for r in rows:
            writer.writerow([
                r["sku"], r["ean"], r["brand"], f"{r['brand']} {r['model']}", r["description"],
                "Herrenjeans", r["size_raw"], r["color"],
                f"{r['price_cents'] / 100:.2f}".replace(".", ","),
                f"{r['list_price_cents'] / 100:.2f}".replace(".", ","),
                random.choices(availability_choices, weights=[80, 15, 5])[0],
                r["image_url"], f"https://belboon-tracking.example.com/out/{r['sku']}",
            ])


def write_tradedoubler_xml(path: Path, n: int = 210):
    rows = list(gen_rows(n, shop_variant_bias=33))
    root = ET.Element("products")
    availability_choices = ["1", "0"]
    for r in rows:
        p = ET.SubElement(root, "product")
        ET.SubElement(p, "sku").text = r["sku"]
        ET.SubElement(p, "ean").text = r["ean"]
        ET.SubElement(p, "brand").text = r["brand"]
        ET.SubElement(p, "title").text = f"{r['brand']} {r['model']}"
        ET.SubElement(p, "description").text = r["description"]
        ET.SubElement(p, "category").text = "Herrenjeans"
        ET.SubElement(p, "size").text = r["size_raw"]
        ET.SubElement(p, "colour").text = r["color"]
        ET.SubElement(p, "price").text = f"{r['price_cents'] / 100:.2f}"
        ET.SubElement(p, "rrp").text = f"{r['list_price_cents'] / 100:.2f}"
        ET.SubElement(p, "in_stock").text = random.choices(availability_choices, weights=[88, 12])[0]
        ET.SubElement(p, "image").text = r["image_url"]
        ET.SubElement(p, "url").text = f"https://td-tracking.example.com/redirect/{r['sku']}"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    write_awin_csv(SAMPLES_DIR / "awin_jeans.csv")
    write_belboon_csv(SAMPLES_DIR / "belboon_jeans.csv")
    write_tradedoubler_xml(SAMPLES_DIR / "tradedoubler_jeans.xml")
    print(f"Sample feeds written to {SAMPLES_DIR}")


if __name__ == "__main__":
    main()
