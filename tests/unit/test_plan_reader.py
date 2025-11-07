from web.backend.plan_reader import _find_scales_in_text, _normalize_scale_label, _guess_sheet_info

def test_scale_regex_and_normalization_samples():
    text = "TITLE BLOCK\nScale 1/8\"=1'-0\"\nAlso shown as 1:100 elsewhere"
    labels = _find_scales_in_text(text)
    assert any("1/8" in lbl for lbl in labels), "Should find architectural inch-based scale"
    assert any("1:100" in lbl for lbl in labels), "Should find metric scale"
    arch_norm = _normalize_scale_label("Scale 1/8\"=1'-0\"")
    metric_norm = _normalize_scale_label("1:100")
    assert arch_norm == "1_8in_per_ft"
    assert metric_norm == "1_to_100"

def test_guess_sheet_info_title_line_and_name_next_line():
    page_text = "A1.01 Architectural Cover Sheet\nGeneral Notes and Legend"
    info = _guess_sheet_info(page_text, page_no=1)
    assert info["page_no"] == 1
    assert info["sheet_id"] == "A1.01"
    assert "General" in (info["sheet_name"] or "")

def test_guess_sheet_info_inline_name():
    page_text = "S2  Structural Framing Plan"
    info = _guess_sheet_info(page_text, page_no=2)
    assert info["sheet_id"] == "S2"
    assert "Framing" in (info["sheet_name"] or "")

# Scaffold for local dev (no-run in CI by default):
def test_extract_plan_features_schema_shape_scaffold():
    assert True  # placeholder; enable real PDF-based test locally if desired
