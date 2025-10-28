"""
JCW Cost Estimator - FastAPI Backend
=====================================
RESTful API for construction cost estimation with ML
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from specification_aware_model import estimate_with_specifications
from ml_continuous_improvement import CostEstimatorML

app = FastAPI(
    title="JCW Cost Estimator API",
    description="Professional construction cost estimation with ML",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML model
ml_model = CostEstimatorML()

# Request/Response Models
class EstimateRequest(BaseModel):
    area_sf: float
    project_type: str  # "residential" or "commercial"
    finish_quality: str  # "economy", "standard", "premium", "luxury"
    design_complexity: str  # "simple", "moderate", "complex", "luxury"
    bedrooms: Optional[int] = 0
    bathrooms: Optional[int] = 0
    garage_bays: Optional[int] = 0
    windows: Optional[int] = 0
    doors: Optional[int] = 0
    special_features: Optional[List[str]] = []

class TrainingProject(BaseModel):
    project_name: str
    area_sf: float
    bedrooms: int
    bathrooms: int
    garage_bays: int
    wall_height: float = 10
    perimeter_lf: float
    roof_area_sf: float
    windows: int
    doors: int
    finish_quality: str
    design_complexity: str
    project_type: str
    has_pool: bool = False
    has_elevator: bool = False
    has_smart_home: bool = False
    stories: int = 1
    year: int = 2025
    actual_cost: float

class EstimateResponse(BaseModel):
    rule_based_estimate: Dict
    ml_estimate: Optional[Dict]
    ensemble_estimate: Dict
    confidence: str

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "JCW Cost Estimator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    training_data = ml_model.load_training_data()
    return {
        "status": "healthy",
        "ml_model_loaded": ml_model.model is not None,
        "training_projects": len(training_data)
    }

@app.post("/estimate", response_model=EstimateResponse)
async def get_estimate(request: EstimateRequest):
    """Get cost estimate using rule-based and ML models"""
    
    try:
        # Rule-based estimate
        rule_estimate = estimate_with_specifications(
            area_sf=request.area_sf,
            project_type=request.project_type,
            finish_quality=request.finish_quality,
            design_complexity=request.design_complexity,
            special_features=request.special_features
        )
        
        # ML estimate (if model trained)
        ml_prediction = None
        ml_metadata = None
        
        if ml_model.model is not None and len(ml_model.load_training_data()) >= 3:
            project_data = {
                'area_sf': request.area_sf,
                'bedrooms': request.bedrooms or 3,
                'bathrooms': request.bathrooms or 2,
                'garage_bays': request.garage_bays or 2,
                'wall_height': 10,
                'perimeter_lf': (request.area_sf ** 0.5) * 4,  # Approximate
                'roof_area_sf': request.area_sf * 1.2,  # Approximate
                'windows': request.windows or int(request.area_sf / 150),
                'doors': request.doors or 10,
                'finish_quality': request.finish_quality,
                'design_complexity': request.design_complexity,
                'project_type': request.project_type,
                'has_pool': 'pool' in str(request.special_features).lower(),
                'has_elevator': 'elevator' in str(request.special_features).lower(),
                'has_smart_home': 'smart' in str(request.special_features).lower(),
                'stories': 1,
                'year': 2025
            }
            
            ml_prediction, ml_metadata = ml_model.predict(project_data)
        
        # Ensemble estimate (weighted average)
        training_count = len(ml_model.load_training_data())
        
        if ml_prediction and training_count >= 10:
            # 70% ML, 30% rule-based when well-trained
            ensemble_cost = ml_prediction * 0.7 + rule_estimate['total_cost'] * 0.3
            confidence = "high"
        elif ml_prediction and training_count >= 3:
            # 30% ML, 70% rule-based when training
            ensemble_cost = ml_prediction * 0.3 + rule_estimate['total_cost'] * 0.7
            confidence = "medium"
        else:
            # 100% rule-based when no ML
            ensemble_cost = rule_estimate['total_cost']
            confidence = "low"
        
        return EstimateResponse(
            rule_based_estimate={
                "total_cost": rule_estimate['total_cost'],
                "cost_per_sf": rule_estimate['cost_per_sf'],
                "hard_costs": rule_estimate['hard_costs']['total_hard'],
                "soft_costs": rule_estimate['soft_costs']['total_soft']
            },
            ml_estimate={
                "total_cost": ml_prediction,
                "cost_per_sf": ml_prediction / request.area_sf if ml_prediction else None,
                "confidence": ml_metadata.get('confidence') if ml_metadata else None
            } if ml_prediction else None,
            ensemble_estimate={
                "total_cost": ensemble_cost,
                "cost_per_sf": ensemble_cost / request.area_sf,
                "method": f"{'hybrid' if ml_prediction else 'rule_based'}",
                "training_projects": training_count
            },
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def add_training_project(project: TrainingProject):
    """Add a completed project to training data"""
    
    try:
        project_dict = project.dict()
        ml_model.update_with_actual(project_dict, project.actual_cost)
        
        training_count = len(ml_model.load_training_data())
        
        return {
            "success": True,
            "message": f"Project '{project.project_name}' added to training data",
            "total_training_projects": training_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/training-data")
async def get_training_data():
    """Get all training projects"""
    
    training_data = ml_model.load_training_data()
    
    return {
        "total_projects": len(training_data),
        "projects": training_data
    }

@app.get("/feature-importance")
async def get_feature_importance():
    """Get ML model feature importance"""
    
    if ml_model.model is None:
        raise HTTPException(status_code=404, detail="Model not trained yet")
    
    importance = ml_model.get_feature_importance()
    
    # Sort by importance
    sorted_importance = sorted(
        importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        "features": [
            {"name": name, "importance": float(imp)}
            for name, imp in sorted_importance
        ]
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    
    training_data = ml_model.load_training_data()
    
    if not training_data:
        return {
            "total_projects": 0,
            "avg_cost_per_sf": None,
            "total_value": None
        }
    
    total_value = sum(p['actual_cost'] for p in training_data)
    avg_cost_per_sf = sum(p['actual_cost'] / p['area_sf'] for p in training_data) / len(training_data)
    
    return {
        "total_projects": len(training_data),
        "avg_cost_per_sf": avg_cost_per_sf,
        "total_value": total_value,
        "project_types": {
            "residential": sum(1 for p in training_data if p['project_type'] == 'residential'),
            "commercial": sum(1 for p in training_data if p['project_type'] == 'commercial')
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
