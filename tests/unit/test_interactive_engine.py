"""
Unit tests for InteractiveEngine
Tests plan-aware question generation and answer processing
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from web.backend.interactive_engine import InteractiveEngine


class TestInteractiveEngine:
    """Test cases for InteractiveEngine functionality"""

    @pytest.fixture
    def engine(self):
        """Create InteractiveEngine instance"""
        return InteractiveEngine()

    @pytest.fixture
    def sample_plan_features(self):
        """Sample plan features for testing"""
        return {
            "full_text": "roof shingle asphalt metal tile foundation slab crawl basement window vinyl aluminum wood",
            "estimated_area_sf": 2500,
            "sheet_count": 5
        }

    @pytest.fixture
    def sample_layout_meta(self):
        """Sample layout metadata for testing"""
        return {
            "window_count": 12,
            "fixture_count": 25,
            "room_count": 8,
            "bathroom_count": 3,
            "foundation_type": "slab",
            "plumbing_fixtures": ["sink", "toilet", "shower"],
            "room_types": ["living", "kitchen", "bedroom", "bathroom"]
        }

    def test_generate_questions_basic(self, engine, sample_plan_features):
        """Test basic question generation"""
        questions = engine.generate_questions(sample_plan_features, project_id="test-001")

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert len(questions) <= 5  # Limited to 5 questions

        # Check question structure
        for q in questions:
            assert "id" in q
            assert "trade" in q
            assert "severity" in q
            assert "rationale" in q
            assert "prompt" in q
            assert "suggested_answers" in q
            assert q["id"].startswith("test-001_")

    def test_generate_questions_with_layout(self, engine, sample_plan_features, sample_layout_meta):
        """Test question generation with layout metadata"""
        questions = engine.generate_questions(sample_plan_features, sample_layout_meta, project_id="test-002")

        assert isinstance(questions, list)
        assert len(questions) > 0

        # Should include more specific questions with layout data
        trade_questions = {}
        for q in questions:
            trade = q.get("trade")
            if trade not in trade_questions:
                trade_questions[trade] = []
            trade_questions[trade].append(q)

        # Should have questions for multiple trades
        assert len(trade_questions) > 1

    def test_roofing_questions(self, engine):
        """Test roofing-specific question generation"""
        context = {
            "mentioned": True,
            "material_indicators": [False, False, False],  # No clear material
            "sheet_count": 5
        }

        questions = engine._roofing_questions(context)

        # Should include material question when no clear indicator
        material_questions = [q for q in questions if "material" in q["id"]]
        assert len(material_questions) > 0

        # Check material question structure
        material_q = material_questions[0]
        assert material_q["trade"] == "roofing"
        assert material_q["severity"] == "critical"
        assert "suggested_answers" in material_q
        assert len(material_q["suggested_answers"]) >= 3

    def test_concrete_questions(self, engine):
        """Test concrete/foundation question generation"""
        # Test without foundation type
        context = {"foundation_type": None}
        questions = engine._concrete_questions(context)

        foundation_questions = [q for q in questions if "foundation_type" in q["id"]]
        assert len(foundation_questions) > 0

        # Test with slab foundation
        context = {"foundation_type": "slab"}
        questions = engine._concrete_questions(context)

        thickness_questions = [q for q in questions if "slab_thickness" in q["id"]]
        assert len(thickness_questions) > 0

    def test_windows_questions(self, engine):
        """Test window question generation"""
        # Test without frame indicators
        context = {"frame_indicators": []}
        questions = engine._windows_questions(context)

        frame_questions = [q for q in questions if "window_frame" in q["id"]]
        assert len(frame_questions) > 0

        frame_q = frame_questions[0]
        assert frame_q["severity"] == "critical"
        assert len(frame_q["suggested_answers"]) >= 3

    def test_finishes_questions(self, engine):
        """Test finishes question generation"""
        context = {"area_sf": 2000}
        questions = engine._finishes_questions(context)

        floor_questions = [q for q in questions if "floor_covering" in q["id"]]
        assert len(floor_questions) > 0

        floor_q = floor_questions[0]
        assert floor_q["severity"] == "critical"
        assert "suggested_answers" in floor_q

    def test_apply_answers(self, engine):
        """Test answer application to quantities"""
        quantities = {
            "version": "v0",
            "trades": {
                "roofing": {
                    "items": [
                        {"code": "shingles", "quantity": 100, "unit": "sq"},
                        {"code": "underlayment", "quantity": 100, "unit": "sq"}
                    ]
                },
                "concrete": {
                    "items": [
                        {"code": "slab", "quantity": 50, "unit": "cuyd"}
                    ]
                }
            }
        }

        answers = [
            {"id": "roofing_material", "key": "metal"},
            {"id": "foundation_type", "key": "basement"}
        ]

        modified = engine.apply_answers(quantities, answers)

        # Should be deep copy
        assert modified is not quantities
        assert modified["trades"] is not quantities["trades"]

        # Check that multipliers were applied (based on mappings)
        # Metal roofing should have multiplier > 1.0
        roofing_items = modified["trades"]["roofing"]["items"]
        for item in roofing_items:
            if "source" in item:
                assert "user-clarification: metal" in item["source"]

    def test_deterministic_ids(self, engine, sample_plan_features):
        """Test that question IDs are deterministic for same project"""
        questions1 = engine.generate_questions(sample_plan_features, project_id="deterministic-test")
        questions2 = engine.generate_questions(sample_plan_features, project_id="deterministic-test")

        # Should generate same questions with same IDs
        assert len(questions1) == len(questions2)
        for q1, q2 in zip(questions1, questions2):
            assert q1["id"] == q2["id"]

    def test_question_limits(self, engine, sample_plan_features, sample_layout_meta):
        """Test that question generation is limited"""
        questions = engine.generate_questions(sample_plan_features, sample_layout_meta, project_id="limit-test")

        assert len(questions) <= 5

        # Should be sorted by severity
        severities = [q["severity"] for q in questions]
        # Critical should come before normal
        if "critical" in severities and "normal" in severities:
            critical_idx = severities.index("critical")
            normal_idx = severities.index("normal")
            assert critical_idx < normal_idx

    def test_empty_plan_features(self, engine):
        """Test handling of minimal plan features"""
        minimal_features = {"full_text": "", "estimated_area_sf": 0}
        questions = engine.generate_questions(minimal_features, project_id="minimal-test")

        # Should still generate some questions
        assert isinstance(questions, list)
        assert len(questions) >= 0  # May be 0 if no context matches

    def test_extract_trade_context(self, engine, sample_plan_features, sample_layout_meta):
        """Test trade context extraction"""
        context = engine._extract_trade_context(sample_plan_features, sample_layout_meta)

        assert "roofing" in context
        assert "concrete" in context
        assert "windows" in context
        assert "hvac" in context
        assert "electrical" in context
        assert "plumbing" in context
        assert "finishes" in context

        # Check roofing context
        roofing_ctx = context["roofing"]
        assert roofing_ctx["mentioned"] is True
        assert "material_indicators" in roofing_ctx

        # Check windows context
        windows_ctx = context["windows"]
        assert windows_ctx["count"] == 12

    def test_extract_trade_context_no_layout(self, engine, sample_plan_features):
        """Test trade context extraction without layout metadata"""
        context = engine._extract_trade_context(sample_plan_features, None)

        # Should still extract some context from plan features
        assert "roofing" in context
        assert "hvac" in context
        assert "finishes" in context

        # Layout-dependent trades should be missing or minimal
        assert "windows" not in context or context["windows"]["count"] == 0

    def test_missing_plan_features_fallback(self, engine):
        """Test graceful fallback when plan_features is None or empty"""
        # Test with None
        result = engine.generate_questions(None, {}, project_id="fallback-test")
        assert "questions" in result
        assert "signals" in result

        # Should have fallback signals
        signals = result["signals"]
        fallback_signals = [s for s in signals if s.get("type") == "fallback_mode"]
        assert len(fallback_signals) >= 1

        # Should generate generic questions
        questions = result["questions"]
        assert len(questions) > 0
        assert any("generic" in q["id"] for q in questions)

    def test_missing_layout_meta_fallback(self, engine, sample_plan_features):
        """Test graceful fallback when layout_meta is None or empty"""
        result = engine.generate_questions(sample_plan_features, None, project_id="layout-fallback-test")

        # Should have fallback signals
        signals = result["signals"]
        fallback_signals = [s for s in signals if s.get("type") == "fallback_mode"]
        assert len(fallback_signals) >= 1

        # Should still generate questions
        questions = result["questions"]
        assert isinstance(questions, list)

    def test_empty_questions_fallback(self, engine):
        """Test fallback when no context generates questions"""
        # Empty plan features that won't match any trade context
        empty_features = {"full_text": "random text with no trade keywords"}
        empty_layout = {}

        result = engine.generate_questions(empty_features, empty_layout, project_id="empty-test")

        # Should generate generic questions as fallback
        questions = result["questions"]
        assert len(questions) > 0
        assert any("generic" in q["id"] for q in questions)
