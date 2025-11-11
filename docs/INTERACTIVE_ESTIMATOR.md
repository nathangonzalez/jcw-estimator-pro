# Interactive Estimator

## Overview
The Interactive Estimator enhances the standard estimation process by analyzing blueprint PDFs to infer likely trades and items, then asking clarifying questions to refine the estimate based on user answers.

## Process Flow
1. **Assess**: Upload PDF → Infer trades → Generate questions
2. **Answer**: User provides answers to questions
3. **Estimate**: Apply answers → Generate refined estimate with collapsed and exploded views

## Question Generation
Questions are generated based on:
- Low confidence inferences (< 0.55 confidence)
- Missing required items (e.g., roofing materials, foundation type)
- Critical cost drivers (roofing, windows, HVAC)

## Answer Influence
Answers modify multipliers from `data/interactive/default_mappings.yaml`:
- Quality: economy (0.9), standard (1.0), premium (1.2)
- Complexity: simple (0.95), normal (1.0), complex (1.15)
- Material toggles: e.g., roofing shingle (1.0) vs metal (1.25)

## Artifacts
- `output/<project>/QUESTIONS.json`: Generated questions
- `output/<project>/ASSESS_RESPONSE.json`: Assessment results
- `output/<project>/ESTIMATE_LINES.csv`: Exploded estimate lines
- `output/<project>/TEMPLATE_ROLLUP.csv`: Collapsed trade totals

## Running
- Assess: `scripts/run_assess.ps1 -ProjectId <id> -PdfPath <path>`
- Estimate: `scripts/run_interactive_estimate.ps1 -ProjectId <id> -PdfPath <path> -AnswersJsonPath <path>`
- Smoke test: `scripts/interactive_smoke.ps1` (requires API running)
