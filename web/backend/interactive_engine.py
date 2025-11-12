"""
Interactive Clarifications Engine
Plan-aware question generation for trade-specific clarifications
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

# Load default mappings
DEFAULT_MAPPINGS_PATH = Path(__file__).parent.parent.parent / "data" / "interactive" / "default_mappings.yaml"
with open(DEFAULT_MAPPINGS_PATH, "r") as f:
    DEFAULT_MAPPINGS = yaml.safe_load(f)

# Load clarifications prompts
PROMPTS_PATH = Path(__file__).parent.parent.parent / "prompts" / "interactive" / "clarifications.md"
with open(PROMPTS_PATH, "r") as f:
    CLARIFICATIONS_PROMPTS = f.read()

class InteractiveEngine:
    """Engine for generating plan-aware clarification questions"""

    def __init__(self):
        self.mappings = DEFAULT_MAPPINGS
        self.prompts = CLARIFICATIONS_PROMPTS

    def generate_questions(self, plan_features: Dict[str, Any], layout_meta: Optional[Dict[str, Any]] = None,
                          project_id: str = "unknown") -> List[Dict[str, Any]]:
        """
        Generate clarification questions based on plan features and layout metadata

        Args:
            plan_features: Extracted plan features (from plan_reader)
            layout_meta: Optional layout analysis metadata
            project_id: Project identifier for deterministic generation

        Returns:
            List of question objects conforming to questions.schema.json
        """
        questions = []

        # Extract trade context from plan features
        trade_context = self._extract_trade_context(plan_features, layout_meta)

        # Generate questions for each trade with low confidence or missing critical items
        for trade, context in trade_context.items():
            trade_questions = self._generate_trade_questions(trade, context, plan_features)
            questions.extend(trade_questions)

        # Sort by severity and limit total questions
        questions.sort(key=lambda q: {"critical": 0, "normal": 1, "nice_to_have": 2}.get(q["severity"], 3))
        questions = questions[:5]  # Limit to 5 questions max

        # Add deterministic IDs based on project_id
        for i, q in enumerate(questions):
            q["id"] = f"{project_id}_{q['id']}_{i}"

        return questions

    def _extract_trade_context(self, plan_features: Dict[str, Any], layout_meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract trade-specific context from plan features"""
        context = {}

        # Roofing context
        full_text = plan_features.get("full_text", "").lower()
        if "roof" in full_text or "shingle" in full_text:
            context["roofing"] = {
                "mentioned": True,
                "material_indicators": ["shingle" in full_text, "metal" in full_text, "tile" in full_text],
                "sheet_count": plan_features.get("sheet_count", 0)
            }

        # Foundation context
        if layout_meta:
            foundation_type = layout_meta.get("foundation_type")
            if foundation_type:
                context["concrete"] = {
                    "foundation_type": foundation_type,
                    "slab_thickness_indicators": layout_meta.get("slab_markers", [])
                }

        # Windows context
        window_count = layout_meta.get("window_count", 0) if layout_meta else 0
        if window_count > 0:
            context["windows"] = {
                "count": window_count,
                "frame_indicators": layout_meta.get("window_frame_markers", [])
            }

        # HVAC context
        area_sf = plan_features.get("estimated_area_sf", 0)
        if area_sf > 0:
            context["hvac"] = {
                "area_sf": area_sf,
                "room_count": layout_meta.get("room_count", 0) if layout_meta else 0
            }

        # Electrical context
        fixture_count = layout_meta.get("fixture_count", 0) if layout_meta else 0
        if fixture_count > 0:
            context["electrical"] = {
                "fixture_count": fixture_count,
                "room_types": layout_meta.get("room_types", [])
            }

        # Plumbing context
        plumbing_fixtures = layout_meta.get("plumbing_fixtures", []) if layout_meta else []
        if plumbing_fixtures:
            context["plumbing"] = {
                "fixtures": plumbing_fixtures,
                "bathroom_count": layout_meta.get("bathroom_count", 0)
            }

        # Finishes context
        if area_sf > 0:
            context["finishes"] = {
                "area_sf": area_sf,
                "room_types": layout_meta.get("room_types", []) if layout_meta else []
            }

        return context

    def _generate_trade_questions(self, trade: str, context: Dict[str, Any], plan_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate questions for a specific trade"""
        questions = []

        if trade == "roofing":
            questions.extend(self._roofing_questions(context))
        elif trade == "concrete":
            questions.extend(self._concrete_questions(context))
        elif trade == "windows":
            questions.extend(self._windows_questions(context))
        elif trade == "hvac":
            questions.extend(self._hvac_questions(context))
        elif trade == "electrical":
            questions.extend(self._electrical_questions(context))
        elif trade == "plumbing":
            questions.extend(self._plumbing_questions(context))
        elif trade == "finishes":
            questions.extend(self._finishes_questions(context))

        return questions

    def _roofing_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate roofing-specific questions"""
        questions = []

        # Material type question
        material_indicators = context.get("material_indicators", [])
        if not any(material_indicators):  # No clear material mentioned
            questions.append({
                "id": "roofing_material",
                "trade": "roofing",
                "severity": "critical",
                "rationale": "Roofing material significantly impacts cost (20-30% swing)",
                "prompt": "What roofing material will be used?",
                "suggested_answers": [
                    {"key": "shingle", "label": "Asphalt Shingle"},
                    {"key": "metal", "label": "Metal Panel"},
                    {"key": "tile", "label": "Clay/Concrete Tile"}
                ]
            })

        # Pitch question if not clear from plan
        questions.append({
            "id": "roofing_pitch",
            "trade": "roofing",
            "severity": "normal",
            "rationale": "Roof pitch affects material quantities and labor",
            "prompt": "What is the roof pitch?",
            "suggested_answers": [
                {"key": "standard", "label": "Standard (4/12 - 6/12)"},
                {"key": "steep", "label": "Steep (7/12+)"},
                {"key": "flat", "label": "Flat/Low-slope"}
            ]
        })

        return questions

    def _concrete_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate concrete/foundation questions"""
        questions = []

        foundation_type = context.get("foundation_type")
        if not foundation_type:
            questions.append({
                "id": "foundation_type",
                "trade": "concrete",
                "severity": "critical",
                "rationale": "Foundation type affects structural cost (15-25% swing)",
                "prompt": "What foundation type will be used?",
                "suggested_answers": [
                    {"key": "slab", "label": "Slab-on-grade"},
                    {"key": "crawl", "label": "Crawl space"},
                    {"key": "basement", "label": "Full basement"}
                ]
            })

        # Slab thickness if slab foundation
        if foundation_type == "slab" or not foundation_type:
            questions.append({
                "id": "slab_thickness",
                "trade": "concrete",
                "severity": "normal",
                "rationale": "Slab thickness affects concrete volume and reinforcement",
                "prompt": "What is the required slab thickness?",
                "suggested_answers": [
                    {"key": "4in", "label": "4 inches"},
                    {"key": "6in", "label": "6 inches"},
                    {"key": "8in", "label": "8 inches"}
                ]
            })

        return questions

    def _windows_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate window-specific questions"""
        questions = []

        frame_indicators = context.get("frame_indicators", [])
        if not frame_indicators:
            questions.append({
                "id": "window_frame",
                "trade": "windows",
                "severity": "critical",
                "rationale": "Window frame material affects cost and performance (10-20% swing)",
                "prompt": "What window frame material will be used?",
                "suggested_answers": [
                    {"key": "vinyl", "label": "Vinyl"},
                    {"key": "aluminum", "label": "Aluminum"},
                    {"key": "wood", "label": "Wood"}
                ]
            })

        questions.append({
            "id": "window_glass",
            "trade": "windows",
            "severity": "normal",
            "rationale": "Glass type affects energy efficiency and cost",
            "prompt": "What glass type will be used?",
            "suggested_answers": [
                {"key": "single", "label": "Single-pane"},
                {"key": "double", "label": "Double-pane"},
                {"key": "triple", "label": "Triple-pane"}
            ]
        })

        return questions

    def _hvac_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate HVAC questions"""
        questions = []

        area_sf = context.get("area_sf", 0)
        if area_sf > 2000:  # Larger homes may need zoning
            questions.append({
                "id": "hvac_zoning",
                "trade": "hvac",
                "severity": "normal",
                "rationale": "Zoning improves comfort and efficiency",
                "prompt": "Will the HVAC system include zoning?",
                "suggested_answers": [
                    {"key": "single", "label": "Single zone"},
                    {"key": "multi", "label": "Multi-zone"}
                ]
            })

        questions.append({
            "id": "hvac_efficiency",
            "trade": "hvac",
            "severity": "normal",
            "rationale": "Efficiency rating affects operating costs",
            "prompt": "What efficiency rating is required?",
            "suggested_answers": [
                {"key": "standard", "label": "Standard efficiency"},
                {"key": "high", "label": "High efficiency (SEER 16+)"}
            ]
        })

        return questions

    def _electrical_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate electrical questions"""
        questions = []

        fixture_count = context.get("fixture_count", 0)
        if fixture_count > 20:  # Higher fixture count suggests larger panel
            questions.append({
                "id": "electrical_panel",
                "trade": "electrical",
                "severity": "normal",
                "rationale": "Panel size must accommodate electrical load",
                "prompt": "What size electrical panel is needed?",
                "suggested_answers": [
                    {"key": "100a", "label": "100 Amp"},
                    {"key": "200a", "label": "200 Amp"},
                    {"key": "400a", "label": "400 Amp"}
                ]
            })

        return questions

    def _plumbing_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate plumbing questions"""
        questions = []

        bathroom_count = context.get("bathroom_count", 0)
        if bathroom_count > 0:
            questions.append({
                "id": "plumbing_fixtures",
                "trade": "plumbing",
                "severity": "normal",
                "rationale": "Fixture grade affects cost and quality (5-15% swing)",
                "prompt": "What grade of plumbing fixtures will be used?",
                "suggested_answers": [
                    {"key": "builder", "label": "Builder grade"},
                    {"key": "premium", "label": "Premium grade"},
                    {"key": "luxury", "label": "Luxury grade"}
                ]
            })

        return questions

    def _finishes_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate finishes questions"""
        questions = []

        area_sf = context.get("area_sf", 0)
        if area_sf > 0:
            questions.append({
                "id": "floor_covering",
                "trade": "finishes",
                "severity": "critical",
                "rationale": "Floor covering significantly impacts cost (10-20% swing)",
                "prompt": "What floor covering will be used?",
                "suggested_answers": [
                    {"key": "carpet", "label": "Carpet"},
                    {"key": "tile", "label": "Ceramic Tile"},
                    {"key": "hardwood", "label": "Hardwood"}
                ]
            })

        return questions

    def apply_answers(self, quantities: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply user answers to quantities, adding source tracking

        Args:
            quantities: M01 v0 quantities object
            answers: List of answer objects with id, key/text

        Returns:
            Modified quantities with user-clarification sources
        """
        modified_quantities = json.loads(json.dumps(quantities))  # Deep copy

        for answer in answers:
            q_id = answer.get("id", "")
            key = answer.get("key") or answer.get("text", "")

            # Apply material toggles from mappings
            if "roofing_material" in q_id:
                multiplier = self.mappings["material_toggles"]["roofing"].get(key, 1.0)
                self._apply_trade_multiplier(modified_quantities, "roofing", multiplier, f"user-clarification: {key}")

            elif "foundation_type" in q_id:
                multiplier = self.mappings["material_toggles"]["foundation"].get(key, 1.0)
                self._apply_trade_multiplier(modified_quantities, "concrete", multiplier, f"user-clarification: {key}")

            elif "window_frame" in q_id:
                multiplier = self.mappings["material_toggles"]["windows"].get(key, 1.0)
                self._apply_trade_multiplier(modified_quantities, "windows", multiplier, f"user-clarification: {key}")

        return modified_quantities

    def _apply_trade_multiplier(self, quantities: Dict[str, Any], trade: str, multiplier: float, source: str):
        """Apply multiplier to trade items with source tracking"""
        if "trades" not in quantities:
            return

        trades = quantities["trades"]
        if trade in trades:
            for item in trades[trade].get("items", []):
                if "quantity" in item and item["quantity"] > 0:
                    item["quantity"] *= multiplier
                    item["source"] = source
