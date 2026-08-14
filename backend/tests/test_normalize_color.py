import pytest

from app.normalize.color import normalize_color

VALID_CASES = [
    ("dunkelblau", "dark_blue"),
    ("DUNKELBLAU", "dark_blue"),
    ("dark blue", "dark_blue"),
    ("navy", "dark_blue"),
    ("hellblau", "light_blue"),
    ("light blue", "light_blue"),
    ("mittelblau", "mid_blue"),
    ("medium blue", "mid_blue"),
    ("schwarz", "black"),
    ("SCHWARZ", "black"),
    ("grau", "grey"),
    ("gray", "grey"),
    ("indigo", "indigo"),
    ("khaki", "khaki"),
    ("  Khaki  ", "khaki"),
]


@pytest.mark.parametrize("raw,expected", VALID_CASES)
def test_maps_known_spellings_to_canonical(raw, expected):
    assert normalize_color(raw) == expected


def test_unknown_color_is_passed_through_lowercased_and_logged(caplog):
    with caplog.at_level("WARNING", logger="sizehive.normalize.color"):
        assert normalize_color("Burgundy") == "burgundy"
    assert "unmapped color spelling" in caplog.text
