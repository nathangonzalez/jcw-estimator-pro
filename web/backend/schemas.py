from typing import Dict, List, Optional
from pydantic import BaseModel, Field, conint, confloat

# ---- Request ----
class BlueprintAnalysis(BaseModel):
    scale: Optional[str] = Field(None, description="e.g. 1/8\"=1'-0\" or 1:100")
    sheet_name: Optional[str] = None
    measured: Optional[Dict[str, float]] = Field(default=None, description="Key dimensional takeoffs in real units")

class EstimateRequest(BaseModel):
    area_sqft: confloat(gt=0) = Field(..., description="Total conditioned floor area in square feet")
    bedrooms: conint(ge=0) = 0
    bathrooms: confloat(ge=0) = 0
    quality: str = Field("standard", description="one of: standard|premium|lux")
    complexity: conint(ge=1, le=5) = 3
    location_zip: Optional[str] = Field(None, description="US ZIP for regional factors")
    features: Optional[Dict[str, bool]] = Field(default=None, description="Feature flags, e.g. {'garage': true}")
    blueprint: Optional[BlueprintAnalysis] = None

# ---- Response ----
class CostBreakdown(BaseModel):
    structure: float
    finishes: float
    systems: float
    sitework: float
    overhead_profit: float

class EstimateResponse(BaseModel):
    total_cost: float
    breakdown: CostBreakdown
    confidence: confloat(ge=0, le=1) = 0.65
    model_version: str = "spec-aware-1.0"
    assumptions: List[str] = []
