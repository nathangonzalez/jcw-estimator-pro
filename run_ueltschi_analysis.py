"""
Comprehensive Ueltschi Project Analysis
========================================
Full mathematical analysis with benchmarking and validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dimensional_analysis import (
    Dimension, UnitType, UnitConverter, 
    ScaleInterpreter, GeometryCalculator, DimensionalValidator
)
from scaling_engine import (
    ScalingType, MaterialScaler, StructuralScalingAnalyzer
)
import json
from datetime import datetime

# ============================================================================
# UELTSCHI PROJECT DATA
# ============================================================================
UELTSCHI_DATA = {
    "project_name": "Ueltschi Building",
    "actual_area_sf": 6398,
    "actual_cost": 4827254,
    "actual_cost_per_sf": 754.43,
    "dimensions": {
        "length_ft": 80,  # Estimated from square footage
        "width_ft": 80,   # Estimated from square footage
        "height_ft": 12,  # Typical commercial height
        "stories": 1
    },
    "scale": "1/4\" = 1'-0\"",
    "construction_type": "commercial_renovation",
    "year": 2023
}

# Industry benchmarks (per SF)
BENCHMARKS = {
    "basic_renovation": {"min": 150, "avg": 250, "max": 350},
    "moderate_renovation": {"min": 300, "avg": 450, "max": 600},
    "extensive_renovation": {"min": 600, "avg": 800, "max": 1000},
    "luxury_renovation": {"min": 1000, "avg": 1500, "max": 2500}
}

# Cost factors
COST_FACTORS = {
    "materials": {
        "concrete": {"unit_cost": 150, "unit": "CY", "yield_loss": 0.05},
        "drywall": {"unit_cost": 2.50, "unit": "SF", "yield_loss": 0.10},
        "flooring": {"unit_cost": 8.50, "unit": "SF", "yield_loss": 0.08},
        "electrical": {"unit_cost": 15.00, "unit": "SF", "yield_loss": 0.02},
        "plumbing": {"unit_cost": 12.00, "unit": "SF", "yield_loss": 0.02},
        "hvac": {"unit_cost": 18.00, "unit": "SF", "yield_loss": 0.03},
        "framing": {"unit_cost": 4.50, "unit": "LF", "yield_loss": 0.15}
    },
    "labor": {
        "base_rate": 65.00,  # per hour
        "efficiency_factor": 0.75,  # actual vs. ideal
        "hours_per_sf": 0.8
    },
    "overhead": 0.15,  # 15%
    "profit": 0.10,    # 10%
    "contingency": 0.08  # 8%
}

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def print_subheader(title):
    """Print formatted subsection header"""
    print(f"\n--- {title} " + "-"*(75-len(title)))

def analyze_dimensions():
    """Complete dimensional analysis"""
    print_header("PHASE 1: DIMENSIONAL ANALYSIS")
    
    # Basic dimensions
    length = Dimension(UELTSCHI_DATA["dimensions"]["length_ft"], "ft", UnitType.LENGTH)
    width = Dimension(UELTSCHI_DATA["dimensions"]["width_ft"], "ft", UnitType.LENGTH)
    height = Dimension(UELTSCHI_DATA["dimensions"]["height_ft"], "ft", UnitType.LENGTH)
    
    print_subheader("1.1 Base Dimensions")
    print(f"Building Length: {length.value} {length.unit}")
    print(f"Building Width:  {width.value} {width.unit}")
    print(f"Building Height: {height.value} {height.unit}")
    
    # Unit conversions
    print_subheader("1.2 Unit Conversions")
    
    length_m = UnitConverter.to_metric(length)
    width_m = UnitConverter.to_metric(width)
    height_m = UnitConverter.to_metric(height)
    
    print(f"Length:  {length.value} ft = {length_m.value:.2f} m")
    print(f"Width:   {width.value} ft = {width_m.value:.2f} m")
    print(f"Height:  {height.value} ft = {height_m.value:.2f} m")
    
    # Scale interpretation
    print_subheader("1.3 Scale Analysis")
    scale_factor = ScaleInterpreter.parse_scale(UELTSCHI_DATA["scale"])
    print(f"Blueprint Scale: {UELTSCHI_DATA['scale']}")
    print(f"Scale Factor: {scale_factor:.6f}")
    print(f"Interpretation: 1 inch on blueprint = {1/scale_factor:.2f} feet in reality")
    
    # Geometry calculations
    print_subheader("1.4 Geometric Calculations")
    
    area = GeometryCalculator.rectangle_area(length, width)
    perimeter = GeometryCalculator.rectangle_perimeter(length, width)
    volume = GeometryCalculator.volume_rectangular(length, width, height)
    
    print(f"\nArea Calculations:")
    print(f"  Floor Area:    {area.value:,.2f} {area.unit}")
    print(f"  Actual Area:   {UELTSCHI_DATA['actual_area_sf']:,} SF")
    print(f"  Variance:      {abs(area.value - UELTSCHI_DATA['actual_area_sf'])/UELTSCHI_DATA['actual_area_sf']*100:.2f}%")
    
    print(f"\nPerimeter Calculations:")
    print(f"  Building Perimeter: {perimeter.value:,.2f} {perimeter.unit}")
    
    print(f"\nVolume Calculations:")
    print(f"  Building Volume: {volume.value:,.2f} {volume.unit}")
    
    # Wall area
    wall_area = Dimension(
        2 * (length.value + width.value) * height.value,
        "SF",
        UnitType.AREA
    )
    print(f"  Wall Area: {wall_area.value:,.2f} SF")
    
    return {
        "length": length,
        "width": width,
        "height": height,
        "area": area,
        "perimeter": perimeter,
        "volume": volume,
        "wall_area": wall_area
    }

def analyze_scaling(dimensions):
    """Complete scaling analysis"""
    print_header("PHASE 2: SCALING ANALYSIS")
    
    # Test different scale factors
    scale_factors = [0.8, 0.9, 1.0, 1.1, 1.2]
    
    print_subheader("2.1 Linear Scaling (Perimeter, Trim)")
    print(f"{'Scale':<10} {'Original':<15} {'Scaled':<15} {'Change':<10}")
    print("-" * 60)
    
    base_perimeter = dimensions["perimeter"].value
    for sf in scale_factors:
        scaled = base_perimeter * sf
        change = (scaled - base_perimeter) / base_perimeter * 100
        print(f"{sf:<10.1f} {base_perimeter:>14,.2f} {scaled:>14,.2f} {change:>9.1f}%")
    
    print_subheader("2.2 Area Scaling (Floors, Walls, Roofs)")
    print(f"{'Scale':<10} {'Original':<15} {'Scaled':<15} {'Change':<10}")
    print("-" * 60)
    
    base_area = dimensions["area"].value
    for sf in scale_factors:
        scaled = base_area * (sf ** 2)
        change = (scaled - base_area) / base_area * 100
        print(f"{sf:<10.1f} {base_area:>14,.2f} {scaled:>14,.2f} {change:>9.1f}%")
    
    print_subheader("2.3 Volume Scaling (Concrete, Fill)")
    print(f"{'Scale':<10} {'Original':<15} {'Scaled':<15} {'Change':<10}")
    print("-" * 60)
    
    base_volume = dimensions["volume"].value
    for sf in scale_factors:
        scaled = base_volume * (sf ** 3)
        change = (scaled - base_volume) / base_volume * 100
        print(f"{sf:<10.1f} {base_volume:>14,.2f} {scaled:>14,.2f} {change:>9.1f}%")
    
    # Non-linear effects
    print_subheader("2.4 Non-Linear Structural Effects")
    
    print("\nStructural reinforcement requirements:")
    for sf in scale_factors:
        thickness_factor = StructuralScalingAnalyzer.calculate_structural_factor(sf, "commercial")
        new_thickness = 4 * thickness_factor
        print(f"  Scale {sf:.1f}x: {new_thickness:.2f} inches ({thickness_factor:.3f}x factor)")
    
    print("\nFoundation depth requirements:")
    for sf in scale_factors:
        depth_factor = StructuralScalingAnalyzer.calculate_foundation_depth_factor(sf)
        new_depth = 4 * depth_factor
        print(f"  Scale {sf:.1f}x: {new_depth:.2f} ft depth ({depth_factor:.3f}x factor)")

def calculate_costs(dimensions):
    """Complete cost calculation"""
    print_header("PHASE 3: COST CALCULATION")
    
    area_sf = UELTSCHI_DATA["actual_area_sf"]
    perimeter_lf = dimensions["perimeter"].value
    wall_area_sf = dimensions["wall_area"].value
    
    costs = {}
    
    print_subheader("3.1 Material Costs")
    print(f"{'Material':<20} {'Qty':<12} {'Unit':<8} {'Rate':<12} {'Subtotal':<15}")
    print("-" * 75)
    
    total_materials = 0
    
    # Flooring
    flooring_qty = area_sf * (1 + COST_FACTORS["materials"]["flooring"]["yield_loss"])
    flooring_cost = flooring_qty * COST_FACTORS["materials"]["flooring"]["unit_cost"]
    costs["flooring"] = flooring_cost
    total_materials += flooring_cost
    print(f"{'Flooring':<20} {flooring_qty:>11,.2f} {'SF':<8} ${COST_FACTORS['materials']['flooring']['unit_cost']:>10,.2f} ${flooring_cost:>14,.2f}")
    
    # Drywall
    drywall_qty = wall_area_sf * (1 + COST_FACTORS["materials"]["drywall"]["yield_loss"])
    drywall_cost = drywall_qty * COST_FACTORS["materials"]["drywall"]["unit_cost"]
    costs["drywall"] = drywall_cost
    total_materials += drywall_cost
    print(f"{'Drywall':<20} {drywall_qty:>11,.2f} {'SF':<8} ${COST_FACTORS['materials']['drywall']['unit_cost']:>10,.2f} ${drywall_cost:>14,.2f}")
    
    # Framing
    framing_qty = perimeter_lf * (1 + COST_FACTORS["materials"]["framing"]["yield_loss"])
    framing_cost = framing_qty * COST_FACTORS["materials"]["framing"]["unit_cost"]
    costs["framing"] = framing_cost
    total_materials += framing_cost
    print(f"{'Framing':<20} {framing_qty:>11,.2f} {'LF':<8} ${COST_FACTORS['materials']['framing']['unit_cost']:>10,.2f} ${framing_cost:>14,.2f}")
    
    # Electrical
    electrical_qty = area_sf * (1 + COST_FACTORS["materials"]["electrical"]["yield_loss"])
    electrical_cost = electrical_qty * COST_FACTORS["materials"]["electrical"]["unit_cost"]
    costs["electrical"] = electrical_cost
    total_materials += electrical_cost
    print(f"{'Electrical':<20} {electrical_qty:>11,.2f} {'SF':<8} ${COST_FACTORS['materials']['electrical']['unit_cost']:>10,.2f} ${electrical_cost:>14,.2f}")
    
    # Plumbing
    plumbing_qty = area_sf * (1 + COST_FACTORS["materials"]["plumbing"]["yield_loss"])
    plumbing_cost = plumbing_qty * COST_FACTORS["materials"]["plumbing"]["unit_cost"]
    costs["plumbing"] = plumbing_cost
    total_materials += plumbing_cost
    print(f"{'Plumbing':<20} {plumbing_qty:>11,.2f} {'SF':<8} ${COST_FACTORS['materials']['plumbing']['unit_cost']:>10,.2f} ${plumbing_cost:>14,.2f}")
    
    # HVAC
    hvac_qty = area_sf * (1 + COST_FACTORS["materials"]["hvac"]["yield_loss"])
    hvac_cost = hvac_qty * COST_FACTORS["materials"]["hvac"]["unit_cost"]
    costs["hvac"] = hvac_cost
    total_materials += hvac_cost
    print(f"{'HVAC':<20} {hvac_qty:>11,.2f} {'SF':<8} ${COST_FACTORS['materials']['hvac']['unit_cost']:>10,.2f} ${hvac_cost:>14,.2f}")
    
    print(f"\n{'TOTAL MATERIALS':<52} ${total_materials:>14,.2f}")
    costs["total_materials"] = total_materials
    
    # Labor costs
    print_subheader("3.2 Labor Costs")
    total_hours = area_sf * COST_FACTORS["labor"]["hours_per_sf"]
    effective_hours = total_hours / COST_FACTORS["labor"]["efficiency_factor"]
    labor_cost = effective_hours * COST_FACTORS["labor"]["base_rate"]
    costs["labor"] = labor_cost
    
    print(f"Base Hours Required:     {total_hours:>12,.2f} hrs")
    print(f"Efficiency Factor:       {COST_FACTORS['labor']['efficiency_factor']:>12.2%}")
    print(f"Effective Hours:         {effective_hours:>12,.2f} hrs")
    print(f"Labor Rate:              ${COST_FACTORS['labor']['base_rate']:>11,.2f}/hr")
    print(f"TOTAL LABOR:             ${labor_cost:>14,.2f}")
    
    # Subtotals and markups
    print_subheader("3.3 Project Totals")
    subtotal = total_materials + labor_cost
    overhead = subtotal * COST_FACTORS["overhead"]
    profit = (subtotal + overhead) * COST_FACTORS["profit"]
    contingency = (subtotal + overhead + profit) * COST_FACTORS["contingency"]
    total_estimated = subtotal + overhead + profit + contingency
    
    costs.update({
        "subtotal": subtotal,
        "overhead": overhead,
        "profit": profit,
        "contingency": contingency,
        "total_estimated": total_estimated
    })
    
    print(f"\nMaterials:               ${total_materials:>14,.2f}")
    print(f"Labor:                   ${labor_cost:>14,.2f}")
    print(f"{'─'*40}")
    print(f"Subtotal:                ${subtotal:>14,.2f}")
    print(f"Overhead ({COST_FACTORS['overhead']:.0%}):         ${overhead:>14,.2f}")
    print(f"Profit ({COST_FACTORS['profit']:.0%}):           ${profit:>14,.2f}")
    print(f"Contingency ({COST_FACTORS['contingency']:.0%}):     ${contingency:>14,.2f}")
    print(f"{'═'*40}")
    print(f"TOTAL ESTIMATED:         ${total_estimated:>14,.2f}")
    print(f"\nEstimated $/SF:          ${total_estimated/area_sf:>14,.2f}")
    
    return costs

def compare_with_actual(costs):
    """Compare estimate with actual costs"""
    print_header("PHASE 4: ACTUAL COST COMPARISON")
    
    actual_cost = UELTSCHI_DATA["actual_cost"]
    estimated_cost = costs["total_estimated"]
    variance = estimated_cost - actual_cost
    variance_pct = (variance / actual_cost) * 100
    
    print_subheader("4.1 Cost Comparison")
    print(f"\nActual Cost:             ${actual_cost:>14,.2f}")
    print(f"Estimated Cost:          ${estimated_cost:>14,.2f}")
    print(f"Variance:                ${variance:>14,.2f}")
    print(f"Variance %:              {variance_pct:>14.2f}%")
    
    print_subheader("4.2 Per Square Foot Analysis")
    area_sf = UELTSCHI_DATA["actual_area_sf"]
    actual_per_sf = actual_cost / area_sf
    estimated_per_sf = estimated_cost / area_sf
    
    print(f"\nActual $/SF:             ${actual_per_sf:>14,.2f}")
    print(f"Estimated $/SF:          ${estimated_per_sf:>14,.2f}")
    print(f"Variance $/SF:           ${estimated_per_sf - actual_per_sf:>14,.2f}")
    
    # Cost breakdown comparison
    print_subheader("4.3 Component Analysis")
    print(f"\n{'Component':<20} {'Estimated':<18} {'% of Total':<12}")
    print("-" * 60)
    
    components = [
        ("Materials", costs["total_materials"]),
        ("Labor", costs["labor"]),
        ("Overhead", costs["overhead"]),
        ("Profit", costs["profit"]),
        ("Contingency", costs["contingency"])
    ]
    
    for name, value in components:
        pct = (value / estimated_cost) * 100
        print(f"{name:<20} ${value:>16,.2f} {pct:>11.2f}%")

def benchmark_analysis(costs):
    """Benchmark against industry standards"""
    print_header("PHASE 5: INDUSTRY BENCHMARKING")
    
    area_sf = UELTSCHI_DATA["actual_area_sf"]
    actual_per_sf = UELTSCHI_DATA["actual_cost_per_sf"]
    estimated_per_sf = costs["total_estimated"] / area_sf
    
    print_subheader("5.1 Industry Comparison")
    print(f"\n{'Category':<25} {'Min $/SF':<12} {'Avg $/SF':<12} {'Max $/SF':<12} {'Status':<20}")
    print("-" * 85)
    
    for category, ranges in BENCHMARKS.items():
        if ranges["min"] <= actual_per_sf <= ranges["max"]:
            status = "✓ IN RANGE"
        elif actual_per_sf < ranges["min"]:
            status = "↓ BELOW RANGE"
        else:
            status = "↑ ABOVE RANGE"
        
        print(f"{category.replace('_', ' ').title():<25} "
              f"${ranges['min']:>10,.2f} ${ranges['avg']:>10,.2f} ${ranges['max']:>10,.2f} {status:<20}")
    
    print_subheader("5.2 Project Classification")
    
    if actual_per_sf >= BENCHMARKS["luxury_renovation"]["min"]:
        classification = "LUXURY RENOVATION"
    elif actual_per_sf >= BENCHMARKS["extensive_renovation"]["min"]:
        classification = "EXTENSIVE RENOVATION"
    elif actual_per_sf >= BENCHMARKS["moderate_renovation"]["min"]:
        classification = "MODERATE RENOVATION"
    else:
        classification = "BASIC RENOVATION"
    
    print(f"\nActual Cost/SF:   ${actual_per_sf:,.2f}")
    print(f"Classification:   {classification}")
    
    # Find closest benchmark
    closest_category = min(
        BENCHMARKS.items(),
        key=lambda x: abs(x[1]["avg"] - actual_per_sf)
    )
    
    print(f"\nClosest Match:    {closest_category[0].replace('_', ' ').title()}")
    print(f"Benchmark Avg:    ${closest_category[1]['avg']:,.2f}/SF")
    print(f"Variance:         ${actual_per_sf - closest_category[1]['avg']:,.2f}/SF")

def sensitivity_analysis(costs, dimensions):
    """Perform sensitivity analysis"""
    print_header("PHASE 6: SENSITIVITY ANALYSIS")
    
    area_sf = UELTSCHI_DATA["actual_area_sf"]
    base_cost = costs["total_estimated"]
    
    print_subheader("6.1 Cost Sensitivity to Key Variables")
    
    # Test variations
    variations = [-20, -10, -5, 0, 5, 10, 20]
    
    # Labor rate sensitivity
    print(f"\n{'Labor Rate Change':<20} {'New Rate':<12} {'Total Cost':<18} {'Change':<15}")
    print("-" * 75)
    
    base_labor_rate = COST_FACTORS["labor"]["base_rate"]
    for var in variations:
        new_rate = base_labor_rate * (1 + var/100)
        rate_factor = new_rate / base_labor_rate
        new_cost = base_cost + (costs["labor"] * (rate_factor - 1))
        change = ((new_cost - base_cost) / base_cost) * 100
        
        print(f"{var:>+18}% ${new_rate:>10,.2f} ${new_cost:>16,.2f} {change:>+13.2f}%")
    
    # Material cost sensitivity
    print(f"\n{'Material Cost Change':<20} {'Factor':<12} {'Total Cost':<18} {'Change':<15}")
    print("-" * 75)
    
    for var in variations:
        cost_factor = 1 + var/100
        new_cost = base_cost + (costs["total_materials"] * (cost_factor - 1))
        change = ((new_cost - base_cost) / base_cost) * 100
        
        print(f"{var:>+18}% {cost_factor:>11.3f} ${new_cost:>16,.2f} {change:>+13.2f}%")
    
    print_subheader("6.2 Risk Assessment")
    
    # Calculate best and worst case scenarios
    optimistic = base_cost * 0.85  # 15% below estimate
    pessimistic = base_cost * 1.25  # 25% above estimate
    
    print(f"\nBase Estimate:           ${base_cost:>14,.2f}")
    print(f"Optimistic (-15%):       ${optimistic:>14,.2f}")
    print(f"Pessimistic (+25%):      ${pessimistic:>14,.2f}")
    print(f"\nRange:                   ${pessimistic - optimistic:>14,.2f}")
    print(f"Risk Exposure:           {((pessimistic - optimistic) / base_cost * 100):.1f}% of estimate")

def generate_summary_report(dimensions, costs):
    """Generate executive summary"""
    print_header("EXECUTIVE SUMMARY")
    
    actual_cost = UELTSCHI_DATA["actual_cost"]
    estimated_cost = costs["total_estimated"]
    variance_pct = ((estimated_cost - actual_cost) / actual_cost) * 100
    area_sf = UELTSCHI_DATA["actual_area_sf"]
    
    print(f"""
PROJECT: {UELTSCHI_DATA['project_name']}
DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DIMENSIONS:
  Building Area:     {area_sf:,} SF
  Perimeter:         {dimensions['perimeter'].value:,.0f} LF
  Wall Area:         {dimensions['wall_area'].value:,.0f} SF

ACTUAL COSTS:
  Total:             ${actual_cost:,.2f}
  Per SF:            ${actual_cost/area_sf:,.2f}/SF

ESTIMATED COSTS:
  Materials:         ${costs['total_materials']:,.2f}
  Labor:             ${costs['labor']:,.2f}
  Overhead:          ${costs['overhead']:,.2f}
  Profit:            ${costs['profit']:,.2f}
  Contingency:       ${costs['contingency']:,.2f}
  ────────────────────────────────
  Total:             ${estimated_cost:,.2f}
  Per SF:            ${estimated_cost/area_sf:,.2f}/SF

VARIANCE ANALYSIS:
  Dollar Variance:   ${estimated_cost - actual_cost:,.2f}
  Percent Variance:  {variance_pct:+.2f}%
  
ASSESSMENT:
  Estimation Accuracy: {'EXCELLENT' if abs(variance_pct) < 10 else 'GOOD' if abs(variance_pct) < 20 else 'NEEDS IMPROVEMENT'}
  Project Type:      {UELTSCHI_DATA['construction_type']}
  Benchmark Class:   Extensive Renovation
""")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run complete analysis"""
    print("\n" + "="*80)
    print(" UELTSCHI PROJECT - COMPREHENSIVE COST ANALYSIS")
    print(" JCW Estimator Pro - Professional Grade Analysis System")
    print("="*80)
    
    try:
        # Phase 1: Dimensional Analysis
        dimensions = analyze_dimensions()
        
        # Phase 2: Scaling Analysis
        analyze_scaling(dimensions)
        
        # Phase 3: Cost Calculation
        costs = calculate_costs(dimensions)
        
        # Phase 4: Actual Comparison
        compare_with_actual(costs)
        
        # Phase 5: Benchmarking
        benchmark_analysis(costs)
        
        # Phase 6: Sensitivity Analysis
        sensitivity_analysis(costs, dimensions)
        
        # Final Summary
        generate_summary_report(dimensions, costs)
        
        print("\n" + "="*80)
        print(" ANALYSIS COMPLETE")
        print("="*80 + "\n")
        
        return {
            "dimensions": dimensions,
            "costs": costs,
            "status": "success"
        }
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    results = main()
