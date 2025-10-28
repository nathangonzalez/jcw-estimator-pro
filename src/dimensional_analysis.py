"""
Dimensional Analysis Engine

Handles unit detection, conversion, scale interpretation, and geometric calculations
"""

from typing import Dict, Tuple, Optional, Union
from enum import Enum
import re
from dataclasses import dataclass


class UnitSystem(Enum):
    """Supported unit systems"""
    IMPERIAL = "imperial"
    METRIC = "metric"
    MIXED = "mixed"


class UnitType(Enum):
    """Types of measurements"""
    LENGTH = "length"
    AREA = "area"
    VOLUME = "volume"
    ANGLE = "angle"


@dataclass
class Dimension:
    """Represents a dimension with value and unit"""
    value: float
    unit: str
    unit_type: UnitType
    
    def __str__(self):
        return f"{self.value:,.2f} {self.unit}"


class UnitConverter:
    """Handles unit conversions between different systems"""
    
    # Conversion factors to base units (meters for length, square meters for area, etc.)
    LENGTH_CONVERSIONS = {
        # Metric
        'mm': 0.001,
        'cm': 0.01,
        'm': 1.0,
        'km': 1000.0,
        # Imperial
        'in': 0.0254,
        'ft': 0.3048,
        'yd': 0.9144,
        'mi': 1609.34,
        # Common abbreviations
        '"': 0.0254,  # inches
        "'": 0.3048,  # feet
    }
    
    AREA_CONVERSIONS = {
        # Metric
        'mm2': 1e-6,
        'cm2': 1e-4,
        'm2': 1.0,
        'sm': 1.0,  # square meters
        # Imperial
        'in2': 0.00064516,
        'ft2': 0.092903,
        'sf': 0.092903,  # square feet
        'yd2': 0.836127,
        'ac': 4046.86,  # acres
    }
    
    VOLUME_CONVERSIONS = {
        # Metric
        'mm3': 1e-9,
        'cm3': 1e-6,
        'm3': 1.0,
        'l': 0.001,
        # Imperial
        'in3': 1.6387e-5,
        'ft3': 0.0283168,
        'cf': 0.0283168,  # cubic feet
        'yd3': 0.764555,
        'cy': 0.764555,  # cubic yards
        'gal': 0.00378541,
    }
    
    @classmethod
    def detect_unit(cls, text: str) -> Tuple[Optional[str], Optional[UnitType]]:
        """
        Detect unit from text string
        
        Args:
            text: Text potentially containing unit
            
        Returns:
            Tuple of (unit, unit_type) or (None, None) if not found
        """
        text = text.lower().strip()
        
        # Check length units
        for unit in cls.LENGTH_CONVERSIONS:
            if text.endswith(unit) or text == unit:
                return unit, UnitType.LENGTH
        
        # Check area units
        for unit in cls.AREA_CONVERSIONS:
            if text.endswith(unit) or text == unit:
                return unit, UnitType.AREA
        
        # Check volume units
        for unit in cls.VOLUME_CONVERSIONS:
            if text.endswith(unit) or text == unit:
                return unit, UnitType.VOLUME
        
        return None, None
    
    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert value from one unit to another
        
        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Converted value
        """
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        # Determine unit type
        if from_unit in cls.LENGTH_CONVERSIONS and to_unit in cls.LENGTH_CONVERSIONS:
            # Convert to meters, then to target unit
            meters = value * cls.LENGTH_CONVERSIONS[from_unit]
            return meters / cls.LENGTH_CONVERSIONS[to_unit]
        
        elif from_unit in cls.AREA_CONVERSIONS and to_unit in cls.AREA_CONVERSIONS:
            # Convert to square meters, then to target unit
            sq_meters = value * cls.AREA_CONVERSIONS[from_unit]
            return sq_meters / cls.AREA_CONVERSIONS[to_unit]
        
        elif from_unit in cls.VOLUME_CONVERSIONS and to_unit in cls.VOLUME_CONVERSIONS:
            # Convert to cubic meters, then to target unit
            cu_meters = value * cls.VOLUME_CONVERSIONS[from_unit]
            return cu_meters / cls.VOLUME_CONVERSIONS[to_unit]
        
        else:
            raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")
    
    @classmethod
    def to_imperial(cls, dimension: Dimension) -> Dimension:
        """Convert dimension to imperial system"""
        if dimension.unit_type == UnitType.LENGTH:
            value_ft = cls.convert(dimension.value, dimension.unit, 'ft')
            return Dimension(value_ft, 'ft', UnitType.LENGTH)
        elif dimension.unit_type == UnitType.AREA:
            value_sf = cls.convert(dimension.value, dimension.unit, 'sf')
            return Dimension(value_sf, 'SF', UnitType.AREA)
        elif dimension.unit_type == UnitType.VOLUME:
            value_cy = cls.convert(dimension.value, dimension.unit, 'cy')
            return Dimension(value_cy, 'CY', UnitType.VOLUME)
        return dimension
    
    @classmethod
    def to_metric(cls, dimension: Dimension) -> Dimension:
        """Convert dimension to metric system"""
        if dimension.unit_type == UnitType.LENGTH:
            value_m = cls.convert(dimension.value, dimension.unit, 'm')
            return Dimension(value_m, 'm', UnitType.LENGTH)
        elif dimension.unit_type == UnitType.AREA:
            value_sm = cls.convert(dimension.value, dimension.unit, 'm2')
            return Dimension(value_sm, 'SM', UnitType.AREA)
        elif dimension.unit_type == UnitType.VOLUME:
            value_cm = cls.convert(dimension.value, dimension.unit, 'm3')
            return Dimension(value_cm, 'CM', UnitType.VOLUME)
        return dimension


class ScaleInterpreter:
    """Interprets architectural scales"""
    
    @staticmethod
    def parse_scale(scale_text: str) -> float:
        """
        Parse architectural scale notation
        
        Args:
            scale_text: Scale notation (e.g., "1:100", "1/4\"=1'-0\"")
            
        Returns:
            Scale factor (drawing units per real units)
        """
        scale_text = scale_text.strip().lower()
        
        # Handle ratio notation (1:100)
        if ':' in scale_text:
            parts = scale_text.split(':')
            if len(parts) == 2:
                try:
                    drawing = float(parts[0])
                    real = float(parts[1])
                    return drawing / real
                except ValueError:
                    pass
        
        # Handle architectural notation (1/4"=1'-0")
        if '=' in scale_text:
            parts = scale_text.split('=')
            if len(parts) == 2:
                # Parse left side (drawing)
                drawing_match = re.search(r'(\d+)/(\d+)\s*"', parts[0])
                if drawing_match:
                    drawing_inches = float(drawing_match.group(1)) / float(drawing_match.group(2))
                else:
                    drawing_inches = 1.0
                
                # Parse right side (real)
                real_match = re.search(r"(\d+)(?:'|ft)", parts[1])
                if real_match:
                    real_inches = float(real_match.group(1)) * 12
                else:
                    real_inches = 12.0
                
                return drawing_inches / real_inches
        
        # Handle simple ratio (1/100)
        if '/' in scale_text:
            parts = scale_text.split('/')
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except ValueError:
                    pass
        
        return 1.0  # Default to 1:1 if can't parse


class GeometryCalculator:
    """Calculates geometric properties"""
    
    @staticmethod
    def rectangle_area(length: Dimension, width: Dimension) -> Dimension:
        """Calculate area of rectangle"""
        # Convert to same units
        length_ft = UnitConverter.convert(length.value, length.unit, 'ft')
        width_ft = UnitConverter.convert(width.value, width.unit, 'ft')
        area_sf = length_ft * width_ft
        return Dimension(area_sf, 'SF', UnitType.AREA)
    
    @staticmethod
    def rectangle_perimeter(length: Dimension, width: Dimension) -> Dimension:
        """Calculate perimeter of rectangle"""
        length_ft = UnitConverter.convert(length.value, length.unit, 'ft')
        width_ft = UnitConverter.convert(width.value, width.unit, 'ft')
        perimeter_ft = 2 * (length_ft + width_ft)
        return Dimension(perimeter_ft, 'LF', UnitType.LENGTH)
    
    @staticmethod
    def volume_rectangular(length: Dimension, width: Dimension, height: Dimension) -> Dimension:
        """Calculate volume of rectangular prism"""
        length_ft = UnitConverter.convert(length.value, length.unit, 'ft')
        width_ft = UnitConverter.convert(width.value, width.unit, 'ft')
        height_ft = UnitConverter.convert(height.value, height.unit, 'ft')
        volume_cf = length_ft * width_ft * height_ft
        volume_cy = volume_cf / 27  # Convert to cubic yards
        return Dimension(volume_cy, 'CY', UnitType.VOLUME)
    
    @staticmethod
    def wall_area(perimeter: Dimension, height: Dimension) -> Dimension:
        """Calculate wall area from perimeter and height"""
        perimeter_ft = UnitConverter.convert(perimeter.value, perimeter.unit, 'ft')
        height_ft = UnitConverter.convert(height.value, height.unit, 'ft')
        area_sf = perimeter_ft * height_ft
        return Dimension(area_sf, 'SF', UnitType.AREA)


class DimensionalValidator:
    """Validates dimensions and cross-checks against notes"""
    
    @staticmethod
    def check_consistency(blueprint_dim: Dimension, notes_dim: Dimension, tolerance: float = 0.05) -> Tuple[bool, str]:
        """
        Check if blueprint dimension matches notes dimension within tolerance
        
        Args:
            blueprint_dim: Dimension from blueprint
            notes_dim: Dimension from notes
            tolerance: Acceptable variance (default 5%)
            
        Returns:
            Tuple of (is_consistent, message)
        """
        # Convert to same units for comparison
        bp_value = UnitConverter.convert(blueprint_dim.value, blueprint_dim.unit, 'ft')
        notes_value = UnitConverter.convert(notes_dim.value, notes_dim.unit, 'ft')
        
        variance = abs(bp_value - notes_value) / notes_value if notes_value != 0 else 0
        
        if variance <= tolerance:
            return True, f"✓ Consistent: {blueprint_dim} ≈ {notes_dim} (variance: {variance*100:.1f}%)"
        else:
            return False, f"⚠ MISMATCH: {blueprint_dim} vs {notes_dim} (variance: {variance*100:.1f}%)"
    
    @staticmethod
    def detect_anomalies(dimensions: Dict[str, Dimension]) -> list:
        """
        Detect anomalies in dimensions (e.g., unrealistic ratios)
        
        Args:
            dimensions: Dictionary of dimension name to Dimension
            
        Returns:
            List of anomaly messages
        """
        anomalies = []
        
        # Check for unrealistic building proportions
        if 'length' in dimensions and 'width' in dimensions:
            length_ft = UnitConverter.convert(dimensions['length'].value, dimensions['length'].unit, 'ft')
            width_ft = UnitConverter.convert(dimensions['width'].value, dimensions['width'].unit, 'ft')
            ratio = max(length_ft, width_ft) / min(length_ft, width_ft)
            if ratio > 5:
                anomalies.append(f"⚠ Unusual aspect ratio: {ratio:.1f}:1 (very long/narrow building)")
        
        # Check for unrealistic wall heights
        if 'wall_height' in dimensions:
            height_ft = UnitConverter.convert(dimensions['wall_height'].value, dimensions['wall_height'].unit, 'ft')
            if height_ft < 8:
                anomalies.append(f"⚠ Wall height {height_ft:.1f} ft seems low for residential")
            elif height_ft > 20:
                anomalies.append(f"⚠ Wall height {height_ft:.1f} ft seems high for residential")
        
        return anomalies


def main():
    """Example usage"""
    print("🔍 Dimensional Analysis Engine - Example Usage\n")
    
    # Example 1: Unit conversion
    print("1. Unit Conversion:")
    length_m = Dimension(30.48, 'm', UnitType.LENGTH)
    length_ft = UnitConverter.to_imperial(length_m)
    print(f"   {length_m} = {length_ft}")
    
    area_sm = Dimension(743.2, 'm2', UnitType.AREA)
    area_sf = UnitConverter.to_imperial(area_sm)
    print(f"   {area_sm} = {area_sf}\n")
    
    # Example 2: Scale interpretation
    print("2. Scale Interpretation:")
    scales = ["1:100", "1/4\"=1'-0\"", "1/8\"=1'-0\""]
    for scale in scales:
        factor = ScaleInterpreter.parse_scale(scale)
        print(f"   {scale} = {factor:.6f}")
    print()
    
    # Example 3: Geometry calculation
    print("3. Geometry Calculations:")
    length = Dimension(100, 'ft', UnitType.LENGTH)
    width = Dimension(80, 'ft', UnitType.LENGTH)
    area = GeometryCalculator.rectangle_area(length, width)
    perimeter = GeometryCalculator.rectangle_perimeter(length, width)
    print(f"   Building {length} × {width}")
    print(f"   Area: {area}")
    print(f"   Perimeter: {perimeter}\n")
    
    # Example 4: Validation
    print("4. Dimension Validation:")
    bp_dim = Dimension(100, 'ft', UnitType.LENGTH)
    notes_dim = Dimension(30.5, 'm', UnitType.LENGTH)
    is_consistent, message = DimensionalValidator.check_consistency(bp_dim, notes_dim)
    print(f"   {message}")


if __name__ == '__main__':
    main()
