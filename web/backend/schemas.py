from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, RootModel

# Legacy body
class LegacyEstimateRequest(BaseModel):
    area_sqft: float
    quality: str
    complexity: str

# Module 01 body
class QuantitiesBody(BaseModel):
    version: str = Field(..., pattern="^v0$")
    meta: Optional[Dict[str, Any]] = None
    trades: Dict[str, Any]

class M01EstimateRequest(BaseModel):
    project_id: Optional[str] = None
    quantities: QuantitiesBody
    region: Optional[str] = None
    policy: Optional[str] = None
    unit_costs_csv: Optional[str] = None
    vendor_quotes_csv: Optional[str] = None

class EstimateRequest(RootModel[Dict[str, Any]]):
    """
    Dual-shape shim. If `quantities` present -> treat as M01; else fall back to Legacy.
    """
    # Accept arbitrary keys; validate shape at runtime in route handler.
    root: Dict[str, Any]

# Response (skeleton aligning to estimate_response.schema.json v0)
class LineItemCost(BaseModel):
    code: str
    description: str
    unit: str
    quantity: float
    unit_cost: float
    cost: float
    waste_pct: Optional[float] = None
    labor_pct: Optional[float] = None
    material_pct: Optional[float] = None
    vendor_quote_ref: Optional[str] = None
    notes: Optional[str] = None

class TradeBreakdown(BaseModel):
    subtotal: float
    contingency_cost: Optional[float] = 0
    overhead_cost: Optional[float] = 0
    profit_cost: Optional[float] = 0
    tax_cost: Optional[float] = 0
    line_items: List[LineItemCost] = []

class EstimateResponse(BaseModel):
    version: str = "v0"
    request_id: str
    model_version: Optional[str] = None
    currency: str = "USD"
    total_cost: float
    subtotal_cost: Optional[float] = 0
    contingency_cost: Optional[float] = 0
    overhead_cost: Optional[float] = 0
    profit_cost: Optional[float] = 0
    tax_cost: Optional[float] = 0
    pricing_policy_id: Optional[str] = None
    inputs_digest: Optional[str] = None
    trades: Dict[str, TradeBreakdown] = {}
    assumptions: List[str] = []
    warnings: List[str] = []
    notes: Optional[str] = None
    debug: Optional[Dict[str, Any]] = None
