# JCW Estimator Pro - Advanced Construction Cost Analysis System

## 🎯 Vision
A 10x improvement over basic estimation - professional-grade technical analyst system for construction cost estimation with proper dimensional analysis, scaling, unit conversion, and risk assessment.

## 🚀 Key Features

### 1. **Dimensional Intelligence**
- Automatic unit detection and conversion (mm, cm, in, ft, m)
- Scale interpretation (1:100, 1/4"=1'-0", etc.)
- Geometric computation (linear, area, volume)
- Cross-validation between blueprint dimensions and notes

### 2. **Advanced Scaling Engine**
- Linear scaling (perimeter, trim, piping)
- Area scaling (floors, walls, roofs)
- Volume scaling (foundation, fill, concrete)
- Non-linear effects (structural reinforcement, thickness growth)
- Scaling rules based on engineering principles

### 3. **Cost Calculation Engine**
- Multi-factor cost modeling
- Quantity-dependent pricing
- Regional cost adjustments
- Labor rate variations
- Material yield & scrap factors
- Overhead and profit calculation

### 4. **Correlation & Sensitivity Analysis**
- Multi-variable dependency modeling
- Sensitivity analysis (±% variations)
- Risk assessment and quantification
- Best-guess ranges with confidence intervals
- Key driver identification

### 5. **Quality Assurance**
- Dimension-note cross-checking
- Measurement validation against reference projects
- Anomaly detection
- Variance analysis
- Calibration against actual costs

## 📊 Input Requirements

### Blueprint Data
```json
{
  "dimensions": {
    "building_length": {"value": 100, "unit": "ft"},
    "building_width": {"value": 80, "unit": "ft"},
    "wall_height": {"value": 10, "unit": "ft"}
  },
  "scale": "1/4\" = 1'-0\"",
  "units": "imperial"
}
```

### Cost Data
```json
{
  "line_items": [
    {
      "item": "Concrete",
      "unit_cost": 150,
      "unit": "CY",
      "quantity_breaks": [
        {"min_qty": 0, "max_qty": 50, "multiplier": 1.0},
        {"min_qty": 51, "max_qty": 100, "multiplier": 0.95}
      ]
    }
  ]
}
```

### Correlation Factors
```json
{
  "labor_rate": {"base": 45, "unit": "$/hour", "regional_factor": 1.1},
  "overhead_percentage": 0.10,
  "profit_percentage": 0.05,
  "scrap_factor": 0.05,
  "yield_loss": 0.03
}
```

## 📈 Output Format

### 1. Unit Conversion Summary
```
Original Units: Imperial (ft, in)
Target System: Imperial
Conversions Applied:
  - Building length: 100 ft (30.48 m)
  - Total area: 8,000 SF (743.2 SM)
```

### 2. Scaling Computation
```
Base dimensions: 100 ft × 80 ft
Scale factor: 1.2x
Scaled dimensions: 120 ft × 96 ft
Effects:
  - Linear materials: +20%
  - Area materials: +44%
  - Volume materials: +72.8%
```

### 3. Quantity Take-off
```
Material          Qty    Unit   Method
--------------------------------------
Concrete          125    CY     Volume calc
Rebar             8,500  LF     Area × factor
Lumber            45,000 BF     Linear calc
```

### 4. Cost Breakdown
```
Item              Qty   Unit Cost  Subtotal
-------------------------------------------
Concrete          125   $150       $18,750
Labor             500   $45        $22,500
-------------------------------------------
Subtotal                           $41,250
Overhead (10%)                     $4,125
Profit (5%)                        $2,269
-------------------------------------------
Total                              $47,644
```

### 5. Sensitivity Analysis
```
Factor            Base    -10%      +10%     Impact
----------------------------------------------------
Labor Rate        $45     $42,644   $52,644  ±21%
Scrap Factor      5%      $46,251   $49,037  ±3%
Material Cost     Var     $44,144   $51,144  ±15%
```

### 6. Best-Guess Range
```
Conservative: $51,408 (+8%)
Most Likely:  $47,644
Optimistic:   $44,840 (-6%)

Key Risks:
  - Labor availability (±15% cost impact)
  - Material price volatility (±10% cost impact)
  - Scrap rate variance (±3% cost impact)
```

## 🎯 Calibration with Ueltschi Project

### Reference Data
- **Actual Area:** 6,398 SF
- **Actual Budget:** $4,827,254
- **Cost per SF:** $754.43/SF

### Calibration Process
1. Extract actual measurements from blueprint
2. Calculate estimated costs using system
3. Compare against actual budget
4. Identify variance sources
5. Tune coefficients and factors
6. Validate on other projects

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Input Processing Layer          │
│  • Blueprint Reader                     │
│  • Dimension Extractor                  │
│  • Unit Detector                        │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│       Dimensional Analysis Layer        │
│  • Unit Converter                       │
│  • Scale Interpreter                    │
│  • Geometry Calculator                  │
│  • Validation Engine                    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│          Scaling Engine Layer           │
│  • Linear Scaler                        │
│  • Area Scaler                          │
│  • Volume Scaler                        │
│  • Non-linear Effects                   │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│       Quantity Take-off Layer           │
│  • Material Calculator                  │
│  • Labor Calculator                     │
│  • Equipment Calculator                 │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│         Cost Calculation Layer          │
│  • Unit Cost Resolver                   │
│  • Regional Adjustments                 │
│  • Quantity Breaks                      │
│  • Overhead & Profit                    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Analysis & Reporting Layer         │
│  • Sensitivity Analyzer                 │
│  • Risk Assessor                        │
│  • Variance Calculator                  │
│  • Report Generator                     │
└─────────────────────────────────────────┘
```

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

```python
from estimator_pro import BlueprintAnalyzer

# Initialize analyzer
analyzer = BlueprintAnalyzer(
    blueprint_path="path/to/blueprint.pdf",
    cost_data="path/to/costs.json",
    calibration_data="path/to/ueltschi.json"
)

# Run analysis
result = analyzer.analyze()

# Get detailed report
report = analyzer.generate_report(
    include_sensitivity=True,
    include_risk_analysis=True,
    output_format="excel"
)

print(f"Estimated Cost: ${result.total_cost:,.2f}")
print(f"Range: ${result.conservative:,.2f} - ${result.optimistic:,.2f}")
```

## 📚 Documentation

See `docs/` folder for detailed documentation:
- User Guide
- API Reference
- Calibration Guide
- Best Practices
- Examples

## 🧪 Testing

```bash
pytest tests/
```

## 📊 Calibration Status

| Project   | Area (SF) | Actual Cost | Estimated | Variance |
|-----------|-----------|-------------|-----------|----------|
| Ueltschi  | 6,398     | $4,827,254  | TBD       | TBD      |
| Lynn      | TBD       | TBD         | TBD       | TBD      |

## 🎯 Roadmap

- [x] Core architecture design
- [ ] Dimensional analysis engine
- [ ] Scaling engine
- [ ] Cost calculation engine
- [ ] Sensitivity analysis
- [ ] Calibration with Ueltschi
- [ ] Web interface
- [ ] API endpoints

## 📝 License

Proprietary - JCW Construction

## 👥 Contributors

- Development Team
- Cost Estimators
- Project Managers
