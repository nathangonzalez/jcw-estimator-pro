# Interactive Clarifications Prompts
## Plan-Aware Question Generation

### Core Principles
- Generate questions based on `plan_features` + `layout_meta`
- Focus on trade-specific clarifications (slab thickness, roof type, fixture counts, finishes grade)
- Use deterministic generation for test consistency
- Prioritize questions that impact cost significantly

### Question Categories by Trade

#### Roofing
**Context**: From plan text mentioning "roof", "shingles", "metal roof", or sheet counts
**Questions**:
- Material type: shingle/metal/tile (cost swing: 20-30%)
- Pitch/steepness: standard/steep (affects labor/materials)
- Underlayment: standard/premium (moisture protection)

#### Foundation/Concrete
**Context**: From layout meta showing basement/crawl space indicators
**Questions**:
- Foundation type: slab/crawl/basement (cost swing: 15-25%)
- Slab thickness: 4"/6"/8" (structural requirements)
- Vapor barrier: yes/no (code requirements)

#### Windows & Doors
**Context**: From fixture counts in layout or plan text
**Questions**:
- Frame material: vinyl/aluminum/wood (cost swing: 10-20%)
- Glass type: single/double/triple-pane (energy efficiency)
- Hardware grade: standard/premium (durability)

#### HVAC
**Context**: From room counts and square footage
**Questions**:
- System type: central/ductless/hybrid (efficiency)
- Efficiency rating: standard/high-efficiency (operating costs)
- Zoning: single/multi-zone (comfort/control)

#### Electrical
**Context**: From fixture counts and room types
**Questions**:
- Panel size: 100A/200A/400A (capacity)
- Wiring: copper/aluminum (conductivity/safety)
- Smart home features: basic/advanced (integration)

#### Plumbing
**Context**: From fixture counts (sinks, toilets, showers)
**Questions**:
- Fixture grade: builder/premium/luxury (cost swing: 5-15%)
- Water efficiency: standard/low-flow (savings)
- Rough-in materials: standard/upgraded (durability)

#### Finishes
**Context**: From room designations and square footage
**Questions**:
- Floor covering: carpet/tile/hardwood (cost swing: 10-20%)
- Wall finish: paint/wallpaper/paneling (aesthetics)
- Ceiling: drywall/suspended/acoustic (function)

### Prompt Template

```
Given the following plan features and layout metadata:

Plan Features:
{plan_features_json}

Layout Meta:
{layout_meta_json}

Generate clarification questions for the following trade: {trade}

Requirements:
- Questions must be specific to the trade
- Include cost impact rationale
- Provide suggested answer options
- Prioritize critical questions (high cost swing)
- Use plan context to make questions relevant

Output format: JSON array of question objects matching questions.schema.json
```

### Deterministic Generation Rules
1. Sort inferred items by confidence (lowest first)
2. Generate questions for items below threshold
3. Add trade-specific critical questions
4. Limit to 3-5 questions per assessment
5. Use consistent IDs for test reproducibility

### Vendor RFI Integration
Questions should enable generation of vendor bid RFI packs with:
- Specific material requirements
- Quantity clarifications
- Quality/complexity specifications
- Timeline constraints

### M01 Overlay Rules
When answers are provided:
- Add `source:"user-clarification"` to modified quantities
- Update unit costs based on material toggles
- Adjust quantities for specified options
- Maintain audit trail of changes
