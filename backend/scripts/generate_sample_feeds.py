"""Generate three realistically messy sample feeds for local dev, spanning
three categories (Herrenjeans, T-Shirts, Sneaker).

Simulates three affiliate feeds with different schemas/formats (two CSV
dialects with different column names, one XML), the way real affiliate
networks (Awin, Belboon, Tradedoubler) would actually differ. Deliberately
introduces the messiness M3/M4 need something real to work against: mixed
size notations, missing EANs, attributes only in free-text descriptions,
and inconsistent brand spellings. Multiple categories in the same feed is
also realistic — a real affiliate feed isn't scoped to one category either.

Usage: python scripts/generate_sample_feeds.py
"""
import csv
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.normalize.brand import CANONICAL_BRANDS as BRANDS  # noqa: E402

random.seed(42)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

COLORS = ["dunkelblau", "hellblau", "schwarz", "grau", "indigo", "mittelblau", "khaki"]


def spelled_brand(canon_brand: str) -> str:
    return random.choice(BRANDS[canon_brand])


def maybe_missing_ean() -> str:
    return "" if random.random() < 0.2 else str(random.randint(4_000_000_000_000, 4_999_999_999_999))


def price_pair() -> tuple[int, int]:
    list_price = random.randint(1990, 14990)
    discount = random.random()
    if discount < 0.4:
        price = list_price  # never discounted -> useful for the M7 discount-honesty check
    else:
        price = int(list_price * random.uniform(0.5, 0.95))
    return price, list_price


# ---------------------------------------------------------------- Herrenjeans

# Not every brand in app.normalize.brand.CANONICAL_BRANDS makes sense for
# jeans (Nike/Adidas etc. are sneaker brands in that shared table) — scope
# jeans brands explicitly instead of picking from the whole table.
JEANS_BRANDS = [
    "Levi's", "Wrangler", "Lee", "Diesel", "Tommy Hilfiger", "Calvin Klein",
    "G-Star", "Pepe Jeans", "Jack & Jones", "Nudie Jeans", "Replay", "BOSS",
]
JEANS_MODELS = [
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
JEANS_MATERIALS = [
    ("100% Baumwolle", "Bio-Baumwolle"), ("98% Baumwolle, 2% Elasthan", None),
    ("99% Cotton, 1% Elastane", None), ("100% Cotton", "GOTS zertifiziert"),
    ("80% Baumwolle, 18% Polyester, 2% Elasthan", None),
]
CLOSURES = ["Knopfleiste", "Reißverschluss"]
JEANS_SIZE_FORMATS = [
    lambda w, l: f"W{w}/L{l}",
    lambda w, l: f"{w}/{l}",
    lambda w, l: f"W {w} L {l}",
    lambda w, l: f"{w}x{l}",
]
JEANS_WIDTHS = [28, 29, 30, 31, 32, 33, 34, 36, 38]
JEANS_LENGTHS = [30, 32, 34, 36]


def make_jeans_templates(n: int) -> list[dict]:
    templates = []
    for _ in range(n):
        material, sustainability = random.choice(JEANS_MATERIALS)
        templates.append(dict(
            category="Herrenjeans",
            brand=random.choice(JEANS_BRANDS),
            model=random.choice(JEANS_MODELS),
            fit=random.choice(FITS),
            rise=random.choice(RISES),
            leg_shape=random.choice(LEG_SHAPES),
            wash=random.choice(WASHES),
            material=material,
            sustainability=sustainability,
            closure=random.choice(CLOSURES),
        ))
    return templates


def build_jeans_description(tpl: dict) -> str:
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


def jeans_size_raw() -> str:
    w, l = random.choice(JEANS_WIDTHS), random.choice(JEANS_LENGTHS)
    return random.choice(JEANS_SIZE_FORMATS)(w, l)


# -------------------------------------------------------------------- T-Shirts

TSHIRT_BRANDS = ["Tommy Hilfiger", "Calvin Klein", "Levi's", "Jack & Jones", "BOSS", "G-Star"]
TSHIRT_MODELS = ["Classic Tee", "Basic Crew", "Oversized Tee", "Print Tee", "Polo Shirt", "Longsleeve Tee"]
TSHIRT_FITS = ["oversized", "slim", "relaxed", "regular"]
TSHIRT_FIT_PHRASES = {
    "oversized": ["Oversized Fit", "extra weit geschnitten", "oversize fit"],
    "slim": ["Slim Fit", "schmale Passform"],
    "relaxed": ["Relaxed Fit", "entspannte Passform"],
    "regular": ["Regular Fit", "klassische Passform"],
}
TSHIRT_SLEEVES = ["sleeveless", "long", "short"]
TSHIRT_SLEEVE_PHRASES = {
    "sleeveless": ["Sleeveless", "ärmellos"],
    "long": ["Long Sleeve", "Langarm"],
    "short": ["Short Sleeve", "Kurzarm"],
}
TSHIRT_NECKLINES = ["v_neck", "polo", "crew"]
TSHIRT_NECKLINE_PHRASES = {
    "v_neck": ["V-Neck", "V-Ausschnitt"],
    "polo": ["Polo Kragen", "Polo Collar"],
    "crew": ["Crew Neck", "Rundhalsausschnitt"],
}
TSHIRT_PRINTS = ["graphic", "logo", "striped", "plain"]
TSHIRT_PRINT_PHRASES = {
    "graphic": ["Graphic Print", "Grafik-Print"],
    "logo": ["Logo Print", "Markenlogo"],
    "striped": ["Striped", "gestreift"],
    "plain": ["Plain", "unifarben"],
}
TSHIRT_MATERIALS = [
    ("100% Cotton", None), ("95% Baumwolle, 5% Elasthan", None),
    ("100% Baumwolle", "Bio-Baumwolle"), ("60% Cotton, 40% Polyester", None),
]
TSHIRT_SIZES = ["S", "M", "L", "XL", "XXL"]


def make_tshirt_templates(n: int) -> list[dict]:
    templates = []
    for _ in range(n):
        material, sustainability = random.choice(TSHIRT_MATERIALS)
        templates.append(dict(
            category="T-Shirts",
            brand=random.choice(TSHIRT_BRANDS),
            model=random.choice(TSHIRT_MODELS),
            fit=random.choice(TSHIRT_FITS),
            sleeve=random.choice(TSHIRT_SLEEVES),
            neckline=random.choice(TSHIRT_NECKLINES),
            print=random.choice(TSHIRT_PRINTS),
            material=material,
            sustainability=sustainability,
        ))
    return templates


def build_tshirt_description(tpl: dict) -> str:
    parts = [
        f"{tpl['brand']} {tpl['model']}.",
        f"{random.choice(TSHIRT_FIT_PHRASES[tpl['fit']])}, {random.choice(TSHIRT_SLEEVE_PHRASES[tpl['sleeve']])}.",
        f"{random.choice(TSHIRT_NECKLINE_PHRASES[tpl['neckline']])}, {random.choice(TSHIRT_PRINT_PHRASES[tpl['print']])}.",
        f"Material: {tpl['material']}.",
    ]
    if tpl["sustainability"]:
        parts.append(f"{tpl['sustainability']}.")
    return " ".join(parts)


def tshirt_size_raw() -> str:
    return random.choice(TSHIRT_SIZES)


# --------------------------------------------------------------------- Sneaker

SNEAKER_BRANDS = ["Nike", "Adidas", "Puma", "New Balance", "Vans"]
SNEAKER_MODELS = ["Runner", "Court Classic", "Trail Trainer", "High Top", "Low Top Icon", "Retro Sneaker"]
SNEAKER_UPPERS = ["leather", "suede", "mesh", "canvas", "synthetic"]
SNEAKER_UPPER_PHRASES = {
    "leather": ["Leather Upper", "Leder-Obermaterial"],
    "suede": ["Suede", "Wildleder"],
    "mesh": ["Mesh Upper", "Mesh-Obermaterial"],
    "canvas": ["Canvas Upper", "Canvas-Obermaterial"],
    "synthetic": ["Synthetic Upper", "Synthetik-Obermaterial"],
}
SNEAKER_SOLES = ["air", "foam", "rubber"]
SNEAKER_SOLE_PHRASES = {
    "air": ["Air-Cushioning", "Luftpolster-Sohle"],
    "foam": ["Foam Sole", "Schaumstoffsohle"],
    "rubber": ["Rubber Sole", "Gummisohle"],
}
SNEAKER_CLOSURES = ["velcro", "slip_on", "laces"]
SNEAKER_CLOSURE_PHRASES = {
    "velcro": ["Velcro", "Klettverschluss"],
    "slip_on": ["Slip-On", "ohne Verschluss"],
    "laces": ["Schnürsenkel", "Lace-Up"],
}
SNEAKER_STYLES = ["high_top", "low_top"]
SNEAKER_STYLE_PHRASES = {
    "high_top": ["High-Top", "hoher Schaft"],
    "low_top": ["Low-Top", "niedriger Schaft"],
}
SNEAKER_EU_SIZES = [40, 41, 42, 43, 44, 45, 46]


def make_sneaker_templates(n: int) -> list[dict]:
    templates = []
    for _ in range(n):
        templates.append(dict(
            category="Sneaker",
            brand=random.choice(SNEAKER_BRANDS),
            model=random.choice(SNEAKER_MODELS),
            upper=random.choice(SNEAKER_UPPERS),
            sole=random.choice(SNEAKER_SOLES),
            closure=random.choice(SNEAKER_CLOSURES),
            style=random.choice(SNEAKER_STYLES),
        ))
    return templates


def build_sneaker_description(tpl: dict) -> str:
    parts = [
        f"{tpl['brand']} {tpl['model']}.",
        f"{random.choice(SNEAKER_UPPER_PHRASES[tpl['upper']])}, {random.choice(SNEAKER_SOLE_PHRASES[tpl['sole']])}.",
        f"{random.choice(SNEAKER_CLOSURE_PHRASES[tpl['closure']])}, {random.choice(SNEAKER_STYLE_PHRASES[tpl['style']])}.",
    ]
    return " ".join(parts)


def sneaker_size_raw() -> str:
    return str(random.choice(SNEAKER_EU_SIZES))


# ------------------------------------------------------------------- combined

ALL_TEMPLATES = make_jeans_templates(30) + make_tshirt_templates(30) + make_sneaker_templates(30)
random.shuffle(ALL_TEMPLATES)

BUILDERS = {
    "Herrenjeans": (build_jeans_description, jeans_size_raw),
    "T-Shirts": (build_tshirt_description, tshirt_size_raw),
    "Sneaker": (build_sneaker_description, sneaker_size_raw),
}


def gen_rows(n: int, shop_variant_bias: int):
    """Yield n raw rows sampled from ALL_TEMPLATES with per-shop brand spelling."""
    for i in range(n):
        tpl = ALL_TEMPLATES[(i + shop_variant_bias) % len(ALL_TEMPLATES)]
        build_description, size_raw_fn = BUILDERS[tpl["category"]]
        price, list_price = price_pair()
        yield {
            "sku": f"S{shop_variant_bias}-{i:05d}",
            "ean": maybe_missing_ean(),
            "brand": spelled_brand(tpl["brand"]),
            "model": tpl["model"],
            "category": tpl["category"],
            "description": build_description(tpl),
            "size_raw": size_raw_fn(),
            "color": random.choice(COLORS),
            "price_cents": price,
            "list_price_cents": list_price,
            "image_url": f"https://picsum.photos/seed/{shop_variant_bias}-{i}/400/500",
        }


def write_awin_csv(path: Path, n: int = 260):
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
                r["category"], r["size_raw"], r["color"],
                f"{r['price_cents'] / 100:.2f}", f"{r['list_price_cents'] / 100:.2f}",
                random.choices(availability_choices, weights=[85, 10, 5])[0],
                r["image_url"], f"https://awin-tracking.example.com/click?sku={r['sku']}",
            ])


def write_belboon_csv(path: Path, n: int = 270):
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
                r["category"], r["size_raw"], r["color"],
                f"{r['price_cents'] / 100:.2f}".replace(".", ","),
                f"{r['list_price_cents'] / 100:.2f}".replace(".", ","),
                random.choices(availability_choices, weights=[80, 15, 5])[0],
                r["image_url"], f"https://belboon-tracking.example.com/out/{r['sku']}",
            ])


def write_tradedoubler_xml(path: Path, n: int = 250):
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
        ET.SubElement(p, "category").text = r["category"]
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
