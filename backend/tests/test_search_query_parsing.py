"""The stored querystring of a search agent has to parse into the same
filters the HTTP endpoint would build — otherwise an agent silently watches
something other than the search the user saved."""
from app.api.search import filters_from_query_string


def test_structural_filters_are_parsed():
    filters = filters_from_query_string(
        "category=Herrenjeans&brand=Levi%27s&brand=Replay&color=dark_blue"
        "&size_w=32&size_l=34&price_min=20&price_max=99.5&in_stock_only=true&q=slim"
    )

    assert filters.category == ["Herrenjeans"]
    assert filters.brand == ["Levi's", "Replay"]
    assert filters.color == ["dark_blue"]
    assert filters.size_w == 32
    assert filters.size_l == 34
    assert filters.price_min == 20.0
    assert filters.price_max == 99.5
    assert filters.in_stock_only is True
    assert filters.q == "slim"


def test_leading_question_mark_is_tolerated():
    assert filters_from_query_string("?category=Sneaker").category == ["Sneaker"]


def test_unreserved_params_become_generic_attribute_filters():
    filters = filters_from_query_string("fit=slim&sleeve=short&upper_material=leather")
    assert filters.attrs == {"fit": "slim", "sleeve": "short", "upper_material": "leather"}


def test_reserved_params_never_leak_into_attrs():
    filters = filters_from_query_string("category=Sneaker&sort=price_asc&page=3&page_size=20&fit=slim")
    assert filters.attrs == {"fit": "slim"}


def test_in_stock_only_defaults_to_false():
    assert filters_from_query_string("q=jeans").in_stock_only is False
    assert filters_from_query_string("in_stock_only=false").in_stock_only is False


def test_empty_query_yields_no_filters():
    filters = filters_from_query_string("")
    assert filters.category is None
    assert filters.q is None
    assert filters.attrs == {}


def test_malformed_numbers_drop_the_filter_instead_of_raising():
    # A stored agent query can be stale or hand-edited; the run must survive it.
    filters = filters_from_query_string("size_w=abc&price_min=&price_max=nope&cotton_min=x")
    assert filters.size_w is None
    assert filters.price_min is None
    assert filters.price_max is None
    assert filters.cotton_min is None


def test_material_and_sustainability_keep_their_dedicated_handling():
    filters = filters_from_query_string("cotton_min=90&sustainability=gots")
    assert filters.cotton_min == 90
    assert filters.sustainability == "gots"
    assert filters.attrs == {}
