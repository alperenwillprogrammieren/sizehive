import pytest

from app.normalize.size import parse_size

VALID_CASES = [
    ("W32/L34", (32, 34)),
    ("W32/L32", (32, 32)),
    ("32/34", (32, 34)),
    ("32/32", (32, 32)),
    ("W 32 L 34", (32, 34)),
    ("W 34 L 36", (34, 36)),
    ("32x34", (32, 34)),
    ("34X36", (34, 36)),
    ("w32/l34", (32, 34)),
    ("W32 / L34", (32, 34)),
    ("W32-L34", (32, 34)),
    ("32-34", (32, 34)),
]


@pytest.mark.parametrize("raw,expected", VALID_CASES)
def test_parses_known_notations(raw, expected):
    assert parse_size(raw) == expected


@pytest.mark.parametrize("raw", ["M", "L", "one size", "32", "48", "", "XL/XXL"])
def test_unparseable_returns_none_none_and_logs(raw, caplog):
    with caplog.at_level("WARNING", logger="sizehive.normalize.size"):
        assert parse_size(raw) == (None, None)
    assert "unparseable size" in caplog.text
