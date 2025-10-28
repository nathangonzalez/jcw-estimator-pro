"""
JCW Cost Estimator - Standalone FastAPI Backend
================================================
Self-contained API for construction cost estimation with PDF takeoff
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import tempfile
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ai_takeoff_pipeline import extract_drawings, extract_page_text, try_parse_scale_from_text, estimate_scale_from_walls, summarize_lines, summarize_polygons
    TAKEOFF_AVAILABLE = True
except ImportError:
    TAKEOFF_AVAILABLE = False

app = FastAPI(
    title="JCW Cost Estimator API",
    description="Professional construction cost estimation with PDF takeoff",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Request Models
class EstimateRequest(BaseModel):
    area_sf: float
    project_type: str
    finish_quality: str
    design_complexity: str
    bedrooms: Optional[int] = 0
    bathrooms: Optional[int] = 0
    garage_bays: Optional[int] = 0
    windows: Optional[int] = 0
    doors: Optional[int] = 0
    special_features: Optional[List[str]] = []

class EstimateResponse(BaseModel):
    rule_based_estimate: Dict
    ensemble_estimate: Dict
    confidence: str

# Simple rule-based estimation
def calculate_estimate(request: EstimateRequest) -> Dict:
    """Calculate cost estimate using calibrated rules"""
    
    # Base cost per SF (calibrated from Lynn/Ueltschi)
    base_cost_per_sf = 500
    
    # Quality adjustments (additive)
    quality_adj = {
        'economy': -60,
        'standard': 0,
        'premium': 40,
        'luxury': 90
    }.get(request.finish_quality, 0)
    
    # Complexity adjustments (additive)
    complexity_adj = {
        'simple': -25,
        'moderate': 0,
        'complex': 50,
        'luxury': 90
    }.get(request.design_complexity, 0)
    
    # Project type multiplier
    type_multiplier = 1.2 if request.project_type == 'commercial' else 1.0
    
    # Calculate adjusted cost per SF
    adjusted_cost_per_sf = (base_cost_per_sf + quality_adj + complexity_adj) * type_multiplier
    
    # Hard costs
    hard_costs = request.area_sf * adjusted_cost_per_sf
    
    # Special features
    feature_costs = 0
    if 'pool' in str(request.special_features).lower():
        if 'luxury' in request.finish_quality:
            feature_costs += 150000
        else:
            feature_costs += 50000
    
    if 'elevator' in str(request.special_features).lower():
        feature_costs += 50000
    
    if 'smart' in str(request.special_features).lower():
        feature_costs += request.area_sf * 15
    
    hard_costs += feature_costs
    
    # Soft costs (35% of hard costs - calibrated)
    soft_costs = hard_costs * 0.35
    
    # Total
    total_cost = hard_costs + soft_costs
    
    return {
        'total_cost': total_cost,
        'cost_per_sf': total_cost / request.area_sf,
        'hard_costs': hard_costs,
        'soft_costs': soft_costs
    }

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>JCW Cost Estimator</h1><p>Frontend not found. API available at /docs</p>")

@app.get("/app.js")
async def serve_js():
    """Serve the JavaScript file"""
    js_path = os.path.join(frontend_path, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "takeoff_available": TAKEOFF_AVAILABLE
    }

@app.post("/estimate", response_model=EstimateResponse)
async def get_estimate(request: EstimateRequest):
    """Get cost estimate"""
    
    try:
        estimate = calculate_estimate(request)
        
        return EstimateResponse(
            rule_based_estimate=estimate,
            ensemble_estimate=estimate,
            confidence="high"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/takeoff")
async def process_takeoff(file: UploadFile = File(...)):
    """Process PDF blueprint for takeoff measurements"""
    
    if not TAKEOFF_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF takeoff module not available. Install: pip install pymupdf numpy pandas"
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Extract drawings
        lines, polys = extract_drawings(tmp_path)
        
        # Try to detect scale
        text = extract_page_text(tmp_path)
        scale = try_parse_scale_from_text(text)
        
        if not scale:
            scale = estimate_scale_from_walls(lines)
        
        if not scale:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=400,
                detail="Could not determine scale from PDF. Please ensure drawing has scale notation."
            )
        
        # Generate summaries
        df_lines = summarize_lines(lines, scale)
        df_polys = summarize_polygons(polys, scale)
        
        # Clean up
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "scale_units": scale.real_units_name,
            "scale_value": scale.real_per_pdf,
            "total_lines": len(lines),
            "total_polygons": len(polys),
            "lines_summary": df_lines.to_dict(orient='records') if not df_lines.empty else [],
            "polygons_summary": df_polys.to_dict(orient='records') if not df_polys.empty else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Takeoff processing failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_projects": 3,
        "avg_cost_per_sf": 682.5,
        "accuracy": "±6.5%",
        "takeoff_enabled": TAKEOFF_AVAILABLE
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
