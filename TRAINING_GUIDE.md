# ML Cost Estimator - Training Guide

## Quick Start

### View Current Training Data
```bash
cd ..\jcw-estimator-pro
python train_model.py
# Select option 3
```

### Add a New Project (Interactive)
```bash
python train_model.py
# Select option 1
# Follow the prompts to enter project details
```

### Batch Add Projects (Programmatic)
```python
# Edit train_model.py and add projects to the new_projects list in batch_add_projects()
python train_model.py
# Select option 2
```

---

## Training Workflow

### Step 1: Complete a Project
After construction is complete and you have the actual final cost.

### Step 2: Run the Training Script
```bash
cd jcw-estimator-pro
python train_model.py
```

### Step 3: Add Project Data
Select option 1 (interactive) and enter:
- Project name
- Area (SF)
- Bedrooms, bathrooms, garage bays
- Wall height, perimeter, roof area
- Windows, doors
- Finish quality (economy/standard/premium/luxury)
- Design complexity (simple/moderate/complex/luxury)
- Project type (residential/commercial)
- Special features (pool, elevator, smart home)
- **Actual cost**

### Step 4: Model Automatically Retrains
The system will:
1. Add the project to training data (`data/training_projects.json`)
2. Retrain the ML model on all projects
3. Save the updated model (`models/cost_estimator_ml.pkl`)
4. Show updated accuracy metrics

---

## Example: Adding a Project

```
================================================================================
 ADD NEW PROJECT TO TRAINING DATA
================================================================================

Enter project details:
Project name: Johnson Residence
Total area (SF): 4200
Number of bedrooms: 4
Number of bathrooms: 3
Number of garage bays: 2
Wall height (ft, default 10): 10
Building perimeter (LF): 260
Roof area (SF): 4500
Number of windows: 25
Number of doors: 9
Finish quality (economy/standard/premium/luxury): premium
Design complexity (simple/moderate/complex/luxury): moderate
Project type (residential/commercial): residential
Has pool? (y/n): n
Has elevator? (y/n): n
Has smart home? (y/n): y
Number of stories (default 1): 1
Year (default 2025): 2025
Actual cost ($): 2650000

✅ Model updated successfully!
   Total training projects: 4
```

---

## Batch Training (For Multiple Projects)

### Method 1: Edit train_model.py directly

1. Open `train_model.py`
2. Find the `batch_add_projects()` function
3. Add your projects to the `new_projects` list:

```python
new_projects = [
    {
        'project_name': 'Smith Residence',
        'area_sf': 4500,
        'bedrooms': 4,
        'bathrooms': 3,
        'garage_bays': 2,
        'wall_height': 10,
        'perimeter_lf': 270,
        'roof_area_sf': 4800,
        'windows': 28,
        'doors': 10,
        'finish_quality': 'premium',
        'design_complexity': 'moderate',
        'project_type': 'residential',
        'has_pool': False,
        'has_elevator': False,
        'has_smart_home': True,
        'stories': 1,
        'year': 2025,
        'actual_cost': 2800000
    },
    {
        'project_name': 'Brown Commercial',
        'area_sf': 6000,
        'bedrooms': 0,
        'bathrooms': 4,
        'garage_bays': 0,
        'wall_height': 12,
        'perimeter_lf': 310,
        'roof_area_sf': 6200,
        'windows': 35,
        'doors': 12,
        'finish_quality': 'luxury',
        'design_complexity': 'complex',
        'project_type': 'commercial',
        'has_pool': False,
        'has_elevator': True,
        'has_smart_home': True,
        'stories': 1,
        'year': 2024,
        'actual_cost': 4500000
    },
]
```

4. Run: `python train_model.py` → Select option 2

### Method 2: Python Script

Create a file `add_projects.py`:

```python
from ml_continuous_improvement import CostEstimatorML

ml_model = CostEstimatorML()

projects = [
    # Your projects here...
]

for project in projects:
    ml_model.update_with_actual(project, project['actual_cost'])
    print(f"✅ Added: {project['project_name']}")
```

Run: `python add_projects.py`

---

## Testing Predictions

### Option 1: Using train_model.py
```bash
python train_model.py
# Select option 4
# Enter project details
```

### Option 2: Python Code
```python
from ml_continuous_improvement import CostEstimatorML

ml_model = CostEstimatorML()

test_project = {
    'project_name': 'Test',
    'area_sf': 5000,
    'bedrooms': 4,
    'bathrooms': 3,
    'garage_bays': 2,
    'wall_height': 10,
    'perimeter_lf': 285,
    'roof_area_sf': 5300,
    'windows': 30,
    'doors': 12,
    'finish_quality': 'premium',
    'design_complexity': 'complex',
    'project_type': 'residential',
    'has_pool': True,
    'has_elevator': False,
    'has_smart_home': False,
    'stories': 1,
    'year': 2025
}

prediction, metadata = ml_model.predict(test_project)
print(f"Prediction: ${prediction:,.0f} (${prediction/test_project['area_sf']:.2f}/SF)")
print(f"Confidence: {metadata['confidence']}")
```

---

## Understanding Model Performance

### Training Accuracy
- **MAPE** (Mean Absolute Percentage Error): Lower is better
- **Target**: <5% MAPE on training data
- **Current**: 0.0% (3 projects - needs more data)

### Feature Importance
The model learns which features are most predictive:

```
1. Bedrooms             32.96% ← Most important
2. Area SF              21.47%
3. Perimeter LF         12.30%
4. Wall Height           7.32%
5. Design Complexity     5.72%
```

### Confidence Levels
- **High**: Project similar to training data (3,000-7,000 SF)
- **Medium**: Slightly outside training range (2,000-8,000 SF)
- **Low**: Far from training examples

---

## Best Practices

### 1. Data Quality
✅ Enter accurate final costs (including all change orders)
✅ Be consistent with quality/complexity ratings
✅ Include all project features

### 2. Training Frequency
- **Minimum**: 3 projects to train initial model
- **Recommended**: 10-20 projects for production accuracy
- **Optimal**: 50+ projects for enterprise-grade predictions

### 3. Data Diversity
Train on:
- Different sizes (2,000 - 10,000 SF)
- Different quality levels (economy to luxury)
- Different project types (residential & commercial)
- Different years (account for inflation)

### 4. Model Maintenance
- **Add new projects immediately** after completion
- **Review predictions** quarterly
- **Retrain completely** if market conditions change significantly

---

## Files Generated

### Training Data
- `data/training_projects.json` - All project data

### Model Files
- `models/cost_estimator_ml.pkl` - Trained ML model

### Backups
Models are automatically versioned by training history.

---

## Troubleshooting

### "Module not found: sklearn"
```bash
pip install scikit-learn numpy
```

### "No saved model found"
This is normal on first run. Add at least 3 projects to train initial model.

### "Training MAPE is high"
- Check for data entry errors
- Ensure quality/complexity ratings are consistent
- Add more diverse training examples

### Model predictions seem off
- Check if test project is similar to training data
- Review feature importance - are key features captured?
- Add more training projects in similar range

---

## Integration with Estimating Workflow

### Standard Workflow:
1. **Initial Estimate**: Use specification-aware model
2. **Submit Bid**: Based on rule-based + ML average
3. **Win Project**: Track actual costs during construction
4. **Project Complete**: Add to training data
5. **Model Improves**: Future estimates more accurate

### Continuous Improvement Loop:
```
Estimate → Build → Actual Cost → Train → Better Estimates
    ↑___________________________________________________|
```

---

## Advanced Usage

### Ensemble Prediction
```python
from specification_aware_model import estimate_with_specifications
from ml_continuous_improvement import CostEstimatorML

# Rule-based estimate
rule_estimate = estimate_with_specifications(
    area_sf=5000,
    project_type="residential",
    finish_quality="premium",
    design_complexity="complex"
)

# ML estimate
ml_model = CostEstimatorML()
ml_prediction, _ = ml_model.predict(project_data)

# Weighted average (70% rule, 30% ML when ML has < 10 training examples)
if len(ml_model.load_training_data()) < 10:
    final_estimate = rule_estimate['total_cost'] * 0.7 + ml_prediction * 0.3
else:
    final_estimate = rule_estimate['total_cost'] * 0.3 + ml_prediction * 0.7

print(f"Final Estimate: ${final_estimate:,.0f}")
```

### Export Training Data
```python
import json
from ml_continuous_improvement import CostEstimatorML

ml_model = CostEstimatorML()
data = ml_model.load_training_data()

with open('export_training_data.json', 'w') as f:
    json.dump(data, f, indent=2)
```

---

## Support

For questions or issues:
1. Check this guide first
2. Review example code in `ml_continuous_improvement.py`
3. Check `train_model.py` for interactive examples

**Remember**: The model gets better with every project you add! 🚀
