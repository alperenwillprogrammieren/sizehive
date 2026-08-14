from app.extract.sneakers import SneakerExtractor

extractor = SneakerExtractor()


def test_extracts_upper_sole_closure_style():
    text = "Leather upper, rubber sole, lace-up closure, low-top silhouette."
    result = extractor.extract(text)
    assert result["upper_material"].value == "leather"
    assert result["sole_type"].value == "rubber"
    assert result["closure_type"].value == "laces"
    assert result["style"].value == "low_top"


def test_german_phrases():
    text = "Mesh-Obermaterial, Luftpolster-Sohle, Klettverschluss, hoher Schaft."
    result = extractor.extract(text)
    assert result["upper_material"].value == "mesh"
    assert result["sole_type"].value == "air"
    assert result["closure_type"].value == "velcro"
    assert result["style"].value == "high_top"


def test_unrecognized_text_yields_empty_result():
    assert extractor.extract("Ein Sneaker ohne besondere Merkmale.") == {}
