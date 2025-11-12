import pytest
from web.backend.blueprint_parsers.layout_stage import parse_titleblock, parse_legend

def test_parse_titleblock_basic():
    """Test parsing titleblock text with scale, sheet, project info."""
    text = """
    TITLE BLOCK
    SCALE: 1/8" = 1'-0"
    SHEET: A1
    PROJECT: Sample House
    DATE: 2023-10-01
    """

    result = parse_titleblock(text)

    assert result["scale"] == '1/8"=1\'-0"'
    assert result["sheet"] == "A1"
    assert result["project"] == "Sample House"
    assert result["date"] == "2023-10-01"

def test_parse_titleblock_metric_scale():
    """Test parsing metric scale."""
    text = "SCALE 1:100\nSHEET P1\nPROJECT: Office Building"

    result = parse_titleblock(text)

    assert result["scale"] == "1:100"
    assert result["sheet"] == "P1"
    assert result["project"] == "Office Building"

def test_parse_titleblock_no_matches():
    """Test parsing text with no titleblock info."""
    text = "This is just some random text with no titleblock information."

    result = parse_titleblock(text)

    assert result["scale"] is None
    assert result["sheet"] is None
    assert result["project"] is None
    assert result["date"] is None

def test_parse_legend_basic():
    """Test parsing legend text into symbol-description pairs."""
    text = """
    LEGEND
    WC - Water Closet
    LAV - Lavatory
    HB - Hose Bibb
    """

    items = parse_legend(text)

    expected = [
        {"symbol": "WC", "desc": "Water Closet"},
        {"symbol": "LAV", "desc": "Lavatory"},
        {"symbol": "HB", "desc": "Hose Bibb"}
    ]

    assert len(items) == 3
    for expected_item in expected:
        assert expected_item in items

def test_parse_legend_colon_format():
    """Test parsing legend with colon separators."""
    text = "SYMBOLS:\nTOILET: Bathroom Fixture\nSINK: Kitchen Sink"

    items = parse_legend(text)

    expected = [
        {"symbol": "TOILET", "desc": "Bathroom Fixture"},
        {"symbol": "SINK", "desc": "Kitchen Sink"}
    ]

    assert len(items) == 2
    for expected_item in expected:
        assert expected_item in items

def test_parse_legend_filters_short():
    """Test that very short symbols/descriptions are filtered out."""
    text = "A - B\nX\nY - Very long description here"

    items = parse_legend(text)

    # Should only include the last one with reasonable length
    assert len(items) == 1
    assert items[0] == {"symbol": "Y", "desc": "Very long description here"}

def test_parse_legend_empty():
    """Test parsing empty or irrelevant text."""
    text = ""

    items = parse_legend(text)

    assert items == []

def test_parse_legend_mixed_content():
    """Test parsing legend mixed with other content."""
    text = """
    GENERAL NOTES
    All dimensions are in inches.
    LEGEND:
    WC - Water Closet
    Some other note here.
    LAV - Lavatory
    """

    items = parse_legend(text)

    expected = [
        {"symbol": "WC", "desc": "Water Closet"},
        {"symbol": "LAV", "desc": "Lavatory"}
    ]

    assert len(items) == 2
    for expected_item in expected:
        assert expected_item in items
