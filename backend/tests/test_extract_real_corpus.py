"""Extractor tests built from strings that actually appear in the live feed.

Why this file exists separately from test_extract_{rules,tshirts,sneakers}:
those were written against `scripts/generate_sample_feeds.py` output, which
was generated to contain exactly the phrases the rules look for. That is a
closed loop — it reported ~37 % coverage for attributes that turned out to
be at 0 % once real shop copy arrived. Every string below is copied from a
real product in the imported Unipolar catalogue, so the suite is anchored
to how shops actually write, not to how the fixtures were generated.
"""
from app.extract.common import phrase_in
from app.extract.registry import get_extractor


def extract(category: str, text: str) -> dict:
    return {key: attr.value for key, attr in get_extractor(category).extract(text).items()}


# --------------------------------------------------------------- Damenjeans

def test_womens_specific_fits_are_recognized():
    """"Mom"/"Balloon" are everyday women's-jeans fits and were absent from
    the original men's-only vocabulary."""
    assert extract("Damenjeans", "Evermind Jeanshose Mom Fit.")["fit"] == "mom"
    assert extract("Damenjeans", "MUD Jeans Balloon Fit Jeans Modell: Demi.")["fit"] == "balloon"


def test_high_waist_organic_cotton_jeans():
    got = extract("Damenjeans", "DAWN High Waist Jeans Skinny Fit. High Waist Jeans aus Bio-Baumwolle")
    assert got["fit"] == "skinny"
    assert got["rise"] == "high"
    assert got["fiber"] == "organic_cotton"
    assert "organic_cotton" in got["sustainability"]


def test_german_inflected_leg_shape():
    """The feed writes "mit geradem Bein"; only the nominative "gerades
    Bein" was listed, so this matched nothing."""
    assert extract("Damenjeans", "Jeanshose mit geradem Bein.")["leg_shape"] == "straight"


# ------------------------------------------------------------------ Sneaker

def test_sustainable_sneaker_upper_materials():
    assert extract("Sneaker", "Veganer Sneaker mit dicker Sohle")["upper_material"] == "vegan"
    assert extract("Sneaker", "Allbirds Tencel Sneaker.")["upper_material"] == "tencel"
    assert extract("Sneaker", "Sneaker aus recycelter Baumwolle.")["upper_material"] == "recycled_cotton"
    assert extract("Sneaker", "Mela Woll-Sneaker Modell: Wool Runner")["upper_material"] == "wool"


def test_bio_baumwolle_sneaker_is_cotton_not_wool():
    """Regression: "wolle" is a substring of "Baumwolle", so naive matching
    tagged every organic-cotton sneaker as wool."""
    got = extract("Sneaker", "Ethletic Low Top Sneaker aus Bio-Baumwolle.")
    assert got["upper_material"] == "cotton"
    assert got["style"] == "low_top"


def test_unhyphenated_low_top_and_schnuerschuh():
    """The feed spells it "Low Top" and "Schnürschuh"; the rules only knew
    "low-top" and "Schnürsenkel"."""
    assert extract("Sneaker", "Low Top Sneaker.")["style"] == "low_top"
    assert extract("Sneaker", "Nachhaltiger Schnürschuh.")["closure_type"] == "laces"


def test_chunky_sole_from_german_phrasing():
    assert extract("Sneaker", "Veganer Sneaker mit dicker Sohle")["sole_type"] == "chunky"


# ----------------------------------------------------------------- T-Shirts

def test_tshirt_sustainability_claims():
    """T-Shirts had no sustainability extraction at all, although this
    exact phrasing is on most of the catalogue."""
    got = extract("T-Shirts", "Fair produziertes und Bio-zertifiziertes Damen T-Shirt")
    assert set(got["sustainability"]) == {"organic_certified", "fair_trade"}


def test_tshirt_named_fibers_without_percentages():
    """extract_material only parses compositions ("95 % Baumwolle"); real
    copy names a fibre with no percentage anywhere."""
    assert extract("T-Shirts", "Nachhaltiges T-Shirt aus Ecovero")["fiber"] == "ecovero"
    assert extract("T-Shirts", "Basic Rundhals T-Shirt aus Leinen.")["fiber"] == "linen"
    assert "material" not in extract("T-Shirts", "T-Shirt aus Leinen.")


def test_marketing_claims_are_not_sustainability_tags():
    """"nachhaltig" is an unverifiable self-description. Tagging it next to
    GOTS would make the filter meaningless."""
    assert "sustainability" not in extract("T-Shirts", "Nachhaltiges T-Shirt Modell: Fenna")


# ------------------------------------------------- word-boundary behaviour

def test_phrase_matching_respects_german_compounds_and_inflection():
    assert not phrase_in("bio-baumwolle t-shirt", "wolle")  # compound prepends
    assert phrase_in("aus recycelter baumwolle", "recycelt")  # inflection appends
    assert phrase_in("woll-sneaker modell", "woll-")
    assert phrase_in("merinowolle sneaker", "merino")
