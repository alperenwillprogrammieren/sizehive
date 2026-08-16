from app.recommend import price_proximity, similarity

JEANS = {"fit": "slim", "rise": "high", "leg_shape": "tapered", "wash": "dark", "stretch": True}


def test_identical_attributes_and_price_score_top():
    result = similarity(JEANS, 8000, dict(JEANS), 8000)
    assert result.score == 1.0
    assert result.shared_attributes == ["fit", "leg_shape", "rise", "stretch", "wash"]


def test_shared_attributes_are_reported():
    other = {**JEANS, "wash": "light", "rise": "low"}
    result = similarity(JEANS, 8000, other, 8000)
    assert result.shared_attributes == ["fit", "leg_shape", "stretch"]


def test_more_agreement_scores_higher():
    close = {**JEANS, "wash": "light"}
    far = {"fit": "loose", "rise": "low", "leg_shape": "straight", "wash": "light", "stretch": False}
    assert similarity(JEANS, 8000, close, 8000).score > similarity(JEANS, 8000, far, 8000).score


def test_price_only_breaks_ties():
    same_attrs_close_price = similarity(JEANS, 8000, dict(JEANS), 8200)
    same_attrs_far_price = similarity(JEANS, 8000, dict(JEANS), 15000)
    assert same_attrs_close_price.score > same_attrs_far_price.score
    # Attribute agreement alone must still outrank a mere price match.
    assert same_attrs_far_price.score > similarity(JEANS, 8000, {"fit": "loose"}, 8000).score


def test_no_common_attribute_keys_scores_on_price_alone():
    # A sneaker's vocabulary shares no keys with a jeans' — an identical
    # price must not make them "similar".
    sneaker = {"upper_material": "leather", "sole_type": "rubber"}
    result = similarity(JEANS, 8000, sneaker, 8000)
    assert result.shared_attributes == []
    assert result.score == 0.25  # price term only


def test_non_scalar_attributes_are_ignored():
    base = {"fit": "slim", "material": {"cotton_pct": 98}, "sustainability": ["gots"]}
    other = {"fit": "slim", "material": {"cotton_pct": 50}, "sustainability": []}
    result = similarity(base, 5000, other, 5000)
    assert result.shared_attributes == ["fit"]
    assert result.score == 1.0


def test_empty_attributes_do_not_crash():
    assert similarity({}, 5000, {}, 5000).score == 0.25
    assert similarity({}, 5000, JEANS, 5000).shared_attributes == []


def test_price_proximity_bounds():
    assert price_proximity(8000, 8000) == 1.0
    assert price_proximity(8000, 12000) == 0.5
    assert price_proximity(8000, 16000) == 0.0
    assert price_proximity(8000, 40000) == 0.0  # clamped, never negative
    assert price_proximity(0, 5000) == 0.0  # no division by zero
