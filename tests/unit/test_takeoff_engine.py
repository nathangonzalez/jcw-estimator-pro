import json
from web.backend.blueprint_parsers.pdf_titleblock import find_scale_strings, normalize_scale
from web.backend.takeoff_engine import TakeoffEngine, PdfMeta

def test_find_and_normalize_scale_label_basic():
    text = 'TITLE BLOCK\nSCALE 1/8"=1\'-0"\nSHEET A1'
    labels = find_scale_strings(text)
    assert labels, "Expected to find at least one scale label"
    norm = normalize_scale(labels[0])
    assert norm["label"] is not None
    # 1/8" = 1'-0" -> 96.0 real inches per drawing inch
    assert abs(norm["ratio"] - 96.0) < 1e-6

def test_find_metric_scale():
    text = "General Notes. Scale 1:100 typical."
    labels = find_scale_strings(text)
    assert any("1:100" in l for l in labels)
    metric = normalize_scale("1:100")
    assert abs(metric["ratio"] - 100.0) < 1e-6

def test_detect_fixtures_keyword_count():
    eng = TakeoffEngine()
    text_pages = ["Plumbing: provide toilet (WC) and lavatory (LAV).", "Fixtures: sink and shower, hose bibb."]
    res = eng.detect_fixtures(text_pages)
    # Should count a few keywords; exact value not critical, but > 0 is expected.
    assert res["fixtures"] > 0
    assert ("legend:fixtures:found" in res.get("signals", [])) == (res["fixtures"] > 0)

def test_to_quantities_structure():
    eng = TakeoffEngine()
    meta = PdfMeta(project_id="UNIT-TEST", source_pdf="sample.pdf", pages_scanned=2)
    geom = {"wall_lf": 450.0, "slab_sf": 1200.0, "signals": ["geometry:fallback"]}
    fixtures = {"fixtures": 12, "signals": ["legend:fixtures:found"]}
    scale = {"scale_label": '1/8"=1\'-0"', "ratio": 96.0, "signals": ["titleblock:scale:found"]}

    q = eng.to_quantities("UNIT-TEST", meta, geom, fixtures, scale)

    # Must be v0 and include trades with items, matching the authoritative schema fields/units casing.
    assert q["version"] == "v0"
    assert "trades" in q and isinstance(q["trades"], dict)
    assert "concrete" in q["trades"]
    assert "framing" in q["trades"]
    assert "plumbing" in q["trades"]

    # Units are lower-case per schema: sf, lf, ea
    concrete_items = q["trades"]["concrete"]["items"]
    framing_items = q["trades"]["framing"]["items"]
    plumbing_items = q["trades"]["plumbing"]["items"]

    assert concrete_items and concrete_items[0]["unit"] == "sf"
    assert framing_items and framing_items[0]["unit"] == "lf"
    assert plumbing_items and plumbing_items[0]["unit"] == "ea"

    # Quantities should be non-negative
    assert concrete_items[0]["quantity"] >= 0
    assert framing_items[0]["quantity"] >= 0
    assert plumbing_items[0]["quantity"] >= 0
