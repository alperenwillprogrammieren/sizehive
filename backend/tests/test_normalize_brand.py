import pytest

from app.normalize.brand import normalize_brand

VALID_CASES = [
    ("Levi's", "Levi's"),
    ("LEVIS", "Levi's"),
    ("Levi Strauss & Co.", "Levi's"),
    ("WRANGLER", "Wrangler"),
    ("Lee", "Lee"),
    ("LEE Jeans", "Lee"),
    ("DIESEL", "Diesel"),
    ("Tommy Hilfiger Denim", "Tommy Hilfiger"),
    ("CK", "Calvin Klein"),
    ("G STAR", "G-Star"),
    ("JACK JONES", "Jack & Jones"),
    ("Hugo Boss", "BOSS"),
    ("  nudie  ", "Nudie Jeans"),
]


@pytest.mark.parametrize("raw,expected", VALID_CASES)
def test_maps_known_spellings_to_canonical(raw, expected):
    assert normalize_brand(raw) == expected


def test_unknown_brand_is_passed_through_trimmed_and_logged(caplog):
    with caplog.at_level("WARNING", logger="sizehive.normalize.brand"):
        assert normalize_brand("  Some New Brand  ") == "Some New Brand"
    assert "unmapped brand spelling" in caplog.text
