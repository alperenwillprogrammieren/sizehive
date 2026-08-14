from app.extract.rules import RuleBasedExtractor

extractor = RuleBasedExtractor()


def test_extracts_fit_rise_leg_shape_wash_from_mixed_de_en_text():
    text = (
        "Levi's 511 Slim. Slim Fit, high rise. Bootcut, dark wash. "
        "Material: 98% Baumwolle, 2% Elasthan. Verschluss: Knopfleiste."
    )
    result = extractor.extract(text)
    assert result["fit"].value == "slim"
    assert result["rise"].value == "high"
    assert result["leg_shape"].value == "bootcut"
    assert result["wash"].value == "dark"
    assert result["closure"].value == "button_fly"
    assert result["material"].value == {"cotton_pct": 98, "elastane_pct": 2}
    assert result["stretch"].value is True
    for attr in result.values():
        assert attr.source == "rule"
        assert 0.0 < attr.confidence <= 1.0


def test_german_only_phrases_are_recognized():
    text = "weites Bein, tief sitzend, verjüngtes Bein, ungewaschen. Reißverschluss."
    result = extractor.extract(text)
    assert result["fit"].value == "loose"
    assert result["rise"].value == "low"
    assert result["leg_shape"].value == "tapered"
    assert result["wash"].value == "raw"
    assert result["closure"].value == "zip_fly"


def test_no_material_percentage_means_no_material_or_stretch_key():
    result = extractor.extract("Straight Fit, Regular Waist, Straight Leg, Black Denim.")
    assert "material" not in result
    assert "stretch" not in result


def test_sustainability_tags_and_pockets():
    result = extractor.extract("Bio-Baumwolle, GOTS zertifiziert. 5 Taschen.")
    assert set(result["sustainability"].value) == {"organic_cotton", "gots"}
    assert result["pockets"].value == 5


def test_unrecognized_text_yields_empty_result():
    assert extractor.extract("Ganz normaler Text ohne Schlagworte.") == {}
