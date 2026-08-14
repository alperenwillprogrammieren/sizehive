from app.extract.tshirts import TShirtExtractor

extractor = TShirtExtractor()


def test_extracts_fit_sleeve_neckline_print():
    text = "Oversized Fit, Short Sleeve, Crew Neck, Graphic Print. Material: 100% Cotton."
    result = extractor.extract(text)
    assert result["fit"].value == "oversized"
    assert result["sleeve"].value == "short"
    assert result["neckline"].value == "crew"
    assert result["print"].value == "graphic"
    assert result["material"].value == {"cotton_pct": 100}
    assert result["stretch"].value is False


def test_german_phrases():
    text = "Schmale Passform, Langarm, V-Ausschnitt, gestreift. 95% Baumwolle, 5% Elasthan."
    result = extractor.extract(text)
    assert result["fit"].value == "slim"
    assert result["sleeve"].value == "long"
    assert result["neckline"].value == "v_neck"
    assert result["print"].value == "striped"
    assert result["stretch"].value is True


def test_unrecognized_text_yields_empty_result():
    assert extractor.extract("Ein T-Shirt ohne besondere Merkmale.") == {}
