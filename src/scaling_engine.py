"""
Advanced Scaling Engine

Handles scaling of measurements, materials, and costs with proper consideration
of linear, area, volume, and non-linear effects.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from dimensional_analysis import Dimension, UnitType, UnitConverter


class ScalingType(Enum):
    """Types of scaling relationships"""
    LINEAR = "linear"        # Scales 1:1 (perimeter, trim, piping)
    AREA = "area"           # Scales with square (floors, walls, roofs)
    VOLUME = "volume"       # Scales with cube (foundation, fill)
    NON_LINEAR = "non_linear"  # Custom scaling rules


@dataclass
class ScalingRule:
    """Defines how an item scales"""
    item_name: str
    scaling_type: ScalingType
    base_quantity: float
    base_dimension: float  # Reference dimension (e.g., base area)
    exponent: float = None  # For non-linear scaling
    threshold_effects: List[Tuple[float, float]] = None  # [(threshold, multiplier), ...]
    
    def scale(self, new_dimension: float) -> float:
        """
        Calculate scaled quantity
        
        Args:
            new_dimension: New dimension value
            
        Returns:
            Scaled quantity
        """
        if self.base_dimension == 0:
            return self.base_quantity
        
        scale_factor = new_dimension / self.base_dimension
        
        if self.scaling_type == ScalingType.LINEAR:
            scaled_qty = self.base_quantity * scale_factor
        
        elif self.scaling_type == ScalingType.AREA:
            scaled_qty = self.base_quantity * (scale_factor ** 2)
        
        elif self.scaling_type == ScalingType.VOLUME:
            scaled_qty = self.base_quantity * (scale_factor ** 3)
        
        elif self.scaling_type == ScalingType.NON_LINEAR and self.exponent:
            scaled_qty = self.base_quantity * (scale_factor ** self.exponent)
        
        else:
            scaled_qty = self.base_quantity
        
        # Apply threshold effects (e.g., structural reinforcement)
        if self.threshold_effects:
            for threshold, multiplier in self.threshold_effects:
                if new_dimension >= threshold:
                    scaled_qty *= multiplier
        
        return scaled_qty


class StructuralScalingAnalyzer:
    """
    Analyzes non-linear structural effects when scaling buildings
    
    Based on engineering principles:
    - Structural loads scale with volume (weight)
    - Structural capacity scales with cross-sectional area
    - Therefore reinforcement needs increase faster than linear scaling
    """
    
    @staticmethod
    def calculate_structural_factor(scale_factor: float, building_type: str = "residential") -> float:
        """
        Calculate structural reinforcement multiplier
        
        Args:
            scale_factor: Linear scale factor
            building_type: Type of building
            
        Returns:
            Multiplier for structural elements
        """
        if scale_factor <= 1.0:
            return 1.0
        
        # Simplified structural scaling model
        # In reality, this would be much more complex
        if building_type == "residential":
            # For typical residential, structural needs scale approximately with ^1.3
            return scale_factor ** 1.3
        elif building_type == "commercial":
            # Commercial may need more reinforcement
            return scale_factor ** 1.5
        else:
            return scale_factor
    
    @staticmethod
    def calculate_foundation_depth_factor(scale_factor: float) -> float:
        """
        Foundation depth may need to increase non-linearly
        
        Args:
            scale_factor: Linear scale factor
            
        Returns:
            Depth increase factor
        """
        if scale_factor <= 1.0:
            return 1.0
        
        # Foundation depth increases with square root of load increase
        # Load increases with volume (scale^3)
        # So depth increases with scale^1.5
        return scale_factor ** 1.5
    
    @staticmethod
    def calculate_hvac_scaling(scale_factor: float) -> float:
        """
        HVAC capacity scales with volume but efficiency improves with size
        
        Args:
            scale_factor: Linear scale factor
            
        Returns:
            HVAC scaling factor
        """
        # Volume increases with scale^3
        # But efficiency improves by ~10% per doubling
        volume_factor = scale_factor ** 3
        
        # Calculate efficiency improvement
        doublings = math.log2(scale_factor) if scale_factor > 1 else 0
        efficiency_factor = 0.9 ** doublings  # 10% improvement per doubling
        
        return volume_factor * efficiency_factor


class MaterialScaler:
    """Scales material quantities with proper consideration of effects"""
    
    def __init__(self, base_area: float):
        """
        Initialize scaler
        
        Args:
            base_area: Base building area in SF
        """
        self.base_area = base_area
        self.scaling_rules = self._define_scaling_rules()
    
    def _define_scaling_rules(self) -> Dict[str, ScalingRule]:
        """Define how different materials/items scale"""
        rules = {}
        
        # Linear scaling items (scale with perimeter/length)
        linear_items = [
            "exterior_trim",
            "base_molding",
            "crown_molding",
            "gutters",
            "fascia",
            "plumbing_rough_in_piping",
            "electrical_rough_in_wiring"
        ]
        for item in linear_items:
            # Assume linear quantity proportional to square root of area
            base_perimeter = 4 * math.sqrt(self.base_area)
            rules[item] = ScalingRule(
                item_name=item,
                scaling_type=ScalingType.LINEAR,
                base_quantity=base_perimeter,
                base_dimension=math.sqrt(self.base_area)
            )
        
        # Area scaling items
        area_items = [
            "flooring",
            "roofing",
            "drywall",
            "insulation",
            "paint",
            "tile",
            "concrete_slab"
        ]
        for item in area_items:
            rules[item] = ScalingRule(
                item_name=item,
                scaling_type=ScalingType.AREA,
                base_quantity=self.base_area,
                base_dimension=self.base_area
            )
        
        # Volume scaling items
        volume_items = [
            "foundation_excavation",
            "fill_dirt",
            "grading"
        ]
        for item in volume_items:
            rules[item] = ScalingRule(
                item_name=item,
                scaling_type=ScalingType.VOLUME,
                base_quantity=self.base_area * 1.0,  # Assume 1 ft depth
                base_dimension=self.base_area
            )
        
        # Non-linear structural items
        rules["structural_steel"] = ScalingRule(
            item_name="structural_steel",
            scaling_type=ScalingType.NON_LINEAR,
            base_quantity=self.base_area * 0.1,
            base_dimension=self.base_area,
            exponent=1.3,  # Structural scaling exponent
            threshold_effects=[(10000, 1.1)]  # 10% more for large buildings
        )
        
        rules["foundation_depth"] = ScalingRule(
            item_name="foundation_depth",
            scaling_type=ScalingType.NON_LINEAR,
            base_quantity=4.0,  # 4 ft base depth
            base_dimension=self.base_area,
            exponent=1.5  # Depth scaling
        )
        
        return rules
    
    def scale_quantity(self, item_name: str, new_area: float) -> Tuple[float, str]:
        """
        Scale quantity for an item
        
        Args:
            item_name: Name of item to scale
            new_area: New building area
            
        Returns:
            Tuple of (scaled_quantity, explanation)
        """
        if item_name not in self.scaling_rules:
            return 0, f"No scaling rule defined for {item_name}"
        
        rule = self.scaling_rules[item_name]
        
        # Calculate new dimension based on scaling type
        if rule.scaling_type in [ScalingType.LINEAR, ScalingType.NON_LINEAR]:
            new_dimension = math.sqrt(new_area)
        else:
            new_dimension = new_area
        
        scaled_qty = rule.scale(new_dimension)
        
        scale_factor = new_dimension / rule.base_dimension if rule.base_dimension > 0 else 1.0
        
        explanation = f"{rule.scaling_type.value} scaling: {rule.base_quantity:.0f} → {scaled_qty:.0f} (factor: {scale_factor:.2f})"
        
        return scaled_qty, explanation
    
    def scale_all(self, new_area: float) -> Dict[str, Dict]:
        """
        Scale all items
        
        Args:
            new_area: New building area
            
        Returns:
            Dictionary of item results
        """
        results = {}
        
        for item_name in self.scaling_rules:
            scaled_qty, explanation = self.scale_quantity(item_name, new_area)
            results[item_name] = {
                'scaled_quantity': scaled_qty,
                'explanation': explanation,
                'scaling_type': self.scaling_rules[item_name].scaling_type.value
            }
        
        return results


class ScalingReport:
    """Generates detailed scaling reports"""
    
    @staticmethod
    def generate_report(base_area: float, new_area: float, scaler: MaterialScaler) -> str:
        """
        Generate detailed scaling report
        
        Args:
            base_area: Base area
            new_area: New area
            scaler: MaterialScaler instance
            
        Returns:
            Formatted report string
        """
        scale_factor = math.sqrt(new_area / base_area)
        area_factor = new_area / base_area
        
        report = []
        report.append("=" * 80)
        report.append("SCALING ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\nBase Area: {base_area:,.0f} SF")
        report.append(f"New Area:  {new_area:,.0f} SF")
        report.append(f"\nLinear Scale Factor: {scale_factor:.3f}x")
        report.append(f"Area Scale Factor:   {area_factor:.3f}x")
        report.append(f"Volume Scale Factor: {area_factor * scale_factor:.3f}x")
        
        # Structural analysis
        structural_factor = StructuralScalingAnalyzer.calculate_structural_factor(scale_factor)
        foundation_factor = StructuralScalingAnalyzer.calculate_foundation_depth_factor(scale_factor)
        hvac_factor = StructuralScalingAnalyzer.calculate_hvac_scaling(scale_factor)
        
        report.append(f"\n📐 STRUCTURAL EFFECTS:")
        report.append(f"  Structural reinforcement factor: {structural_factor:.3f}x")
        report.append(f"  Foundation depth factor:         {foundation_factor:.3f}x")
        report.append(f"  HVAC capacity factor:            {hvac_factor:.3f}x")
        
        # Material scaling
        results = scaler.scale_all(new_area)
        
        report.append(f"\n📦 MATERIAL SCALING:")
        report.append(f"\n{'Item':<30} {'Type':<12} {'Base Qty':<12} {'New Qty':<12} {'Factor':<8}")
        report.append("-" * 80)
        
        for item_name, data in sorted(results.items()):
            base_qty = scaler.scaling_rules[item_name].base_quantity
            new_qty = data['scaled_quantity']
            factor = new_qty / base_qty if base_qty > 0 else 1.0
            
            report.append(f"{item_name:<30} {data['scaling_type']:<12} {base_qty:<12,.0f} {new_qty:<12,.0f} {factor:<8.3f}x")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Example usage"""
    print("🔄 Advanced Scaling Engine - Example Usage\n")
    
    # Example: Scale from 6,398 SF (Ueltschi) to 8,000 SF
    base_area = 6398
    new_area = 8000
    
    scaler = MaterialScaler(base_area)
    report = ScalingReport.generate_report(base_area, new_area, scaler)
    
    print(report)
    
    # Example: Show HVAC scaling effect
    print("\n\n📊 HVAC Scaling Analysis:")
    for scale in [1.0, 1.25, 1.5, 2.0, 3.0]:
        new_area_test = base_area * (scale ** 2)
        hvac_factor = StructuralScalingAnalyzer.calculate_hvac_scaling(scale)
        print(f"  {scale:.2f}x linear scale ({new_area_test:,.0f} SF): HVAC factor = {hvac_factor:.3f}x")


if __name__ == '__main__':
    main()
