"""
Machine Learning Continuous Improvement Module
================================================
Learns from actual project outcomes to improve future estimates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import pickle

class CostEstimatorML:
    """ML model for cost estimation with continuous learning"""
    
    def __init__(self, model_path='models/cost_estimator_ml.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.training_history = []
        self.load_model()
    
    def extract_features(self, project_data: Dict) -> np.array:
        """Extract features from project data for ML model"""
        features = [
            project_data.get('area_sf', 0),
            project_data.get('bedrooms', 0),
            project_data.get('bathrooms', 0),
            project_data.get('garage_bays', 0),
            project_data.get('wall_height', 10),
            project_data.get('perimeter_lf', 0),
            project_data.get('roof_area_sf', 0),
            project_data.get('windows', 0),
            project_data.get('doors', 0),
            
            # Quality indicators (0-3 scale)
            self._quality_to_numeric(project_data.get('finish_quality', 'standard')),
            self._complexity_to_numeric(project_data.get('design_complexity', 'moderate')),
            self._project_type_to_numeric(project_data.get('project_type', 'residential')),
            
            # Special features (binary)
            1 if project_data.get('has_pool', False) else 0,
            1 if project_data.get('has_elevator', False) else 0,
            1 if project_data.get('has_smart_home', False) else 0,
            
            # Location factors
            project_data.get('stories', 1),
            project_data.get('year', datetime.now().year),
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _quality_to_numeric(self, quality: str) -> int:
        mapping = {'economy': 0, 'standard': 1, 'premium': 2, 'luxury': 3}
        return mapping.get(quality, 1)
    
    def _complexity_to_numeric(self, complexity: str) -> int:
        mapping = {'simple': 0, 'moderate': 1, 'complex': 2, 'luxury': 3}
        return mapping.get(complexity, 1)
    
    def _project_type_to_numeric(self, ptype: str) -> int:
        return 1 if ptype == 'commercial' else 0
    
    def train(self, projects: List[Dict]):
        """Train/retrain model on project data"""
        if len(projects) < 3:
            print("⚠️  Need at least 3 projects to train ML model")
            return
        
        # Extract features and targets
        X = []
        y = []
        
        for project in projects:
            features = self.extract_features(project)
            X.append(features[0])
            y.append(project['actual_cost'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train ensemble model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        
        self.model.fit(X_scaled, y)
        
        # Calculate training accuracy
        predictions = self.model.predict(X_scaled)
        mape = np.mean(np.abs((y - predictions) / y)) * 100
        
        print(f"✅ Model trained on {len(projects)} projects")
        print(f"   Training MAPE: {mape:.1f}%")
        
        # Save training history
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'num_projects': len(projects),
            'mape': float(mape),
            'projects': [p['project_name'] for p in projects]
        })
        
        self.save_model()
    
    def predict(self, project_data: Dict) -> Tuple[float, Dict]:
        """Predict cost for new project"""
        if self.model is None:
            return None, {'error': 'Model not trained yet'}
        
        features = self.extract_features(project_data)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        
        # Estimate confidence based on training data similarity
        confidence = self._estimate_confidence(features, project_data)
        
        return prediction, {
            'confidence': confidence,
            'method': 'machine_learning',
            'model_version': len(self.training_history)
        }
    
    def _estimate_confidence(self, features: np.array, project_data: Dict) -> str:
        """Estimate prediction confidence"""
        # Simple heuristic based on project characteristics
        area = project_data.get('area_sf', 0)
        
        # Check if within training range
        if 3000 <= area <= 7000:
            return 'high'
        elif 2000 <= area <= 8000:
            return 'medium'
        else:
            return 'low'
    
    def update_with_actual(self, project_data: Dict, actual_cost: float):
        """Incremental learning from new actual cost"""
        project_data['actual_cost'] = actual_cost
        
        # Load existing training data
        training_data = self.load_training_data()
        training_data.append(project_data)
        
        # Retrain model
        self.train(training_data)
        
        # Save updated training data
        self.save_training_data(training_data)
        
        print(f"✅ Model updated with {project_data.get('project_name', 'project')}")
        print(f"   Total training examples: {len(training_data)}")
    
    def save_model(self):
        """Save trained model to disk"""
        os.makedirs('models', exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'history': self.training_history
            }, f)
        
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.training_history = data['history']
            print(f"✅ Model loaded from {self.model_path}")
        else:
            print("ℹ️  No saved model found, will train from scratch")
    
    def save_training_data(self, data: List[Dict]):
        """Save training data"""
        os.makedirs('data', exist_ok=True)
        with open('data/training_projects.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_training_data(self) -> List[Dict]:
        """Load training data"""
        if os.path.exists('data/training_projects.json'):
            with open('data/training_projects.json', 'r') as f:
                return json.load(f)
        return []
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None:
            return {}
        
        feature_names = [
            'area_sf', 'bedrooms', 'bathrooms', 'garage_bays', 'wall_height',
            'perimeter_lf', 'roof_area_sf', 'windows', 'doors',
            'finish_quality', 'design_complexity', 'project_type',
            'has_pool', 'has_elevator', 'has_smart_home',
            'stories', 'year'
        ]
        
        importances = self.model.feature_importances_
        
        return dict(zip(feature_names, importances))


def initialize_with_known_projects():
    """Initialize ML model with Lynn and Ueltschi data"""
    ml_model = CostEstimatorML()
    
    # Known projects for initial training
    projects = [
        {
            'project_name': 'Lynn',
            'area_sf': 4974,
            'bedrooms': 4,
            'bathrooms': 4,
            'garage_bays': 3,
            'wall_height': 10,
            'perimeter_lf': 280,
            'roof_area_sf': 5248,
            'windows': 34,
            'doors': 13,
            'finish_quality': 'premium',
            'design_complexity': 'complex',
            'project_type': 'residential',
            'has_pool': True,
            'has_elevator': False,
            'has_smart_home': False,
            'stories': 1,
            'year': 2025,
            'actual_cost': 3106517
        },
        {
            'project_name': 'Ueltschi',
            'area_sf': 6398,
            'bedrooms': 5,
            'bathrooms': 5,
            'garage_bays': 3,
            'wall_height': 12,
            'perimeter_lf': 320,
            'roof_area_sf': 6800,
            'windows': 40,
            'doors': 15,
            'finish_quality': 'luxury',
            'design_complexity': 'luxury',
            'project_type': 'commercial',
            'has_pool': False,
            'has_elevator': False,
            'has_smart_home': True,
            'stories': 1,
            'year': 2023,
            'actual_cost': 4827254
        },
        {
            'project_name': 'Gonzalez',
            'area_sf': 3228,
            'bedrooms': 3,
            'bathrooms': 2,
            'garage_bays': 2,
            'wall_height': 10,
            'perimeter_lf': 227,
            'roof_area_sf': 3873,
            'windows': 10,
            'doors': 9,
            'finish_quality': 'standard',
            'design_complexity': 'moderate',
            'project_type': 'residential',
            'has_pool': False,
            'has_elevator': False,
            'has_smart_home': False,
            'stories': 1,
            'year': 2025,
            'actual_cost': 1800000  # Estimated, will update with actual
        }
    ]
    
    # Train model
    ml_model.train(projects)
    
    # Show feature importance
    print("\n📊 Feature Importance:")
    importance = ml_model.get_feature_importance()
    for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {feature:<20} {imp:.4f}")
    
    return ml_model


def main():
    """Test ML continuous improvement"""
    print("="*80)
    print(" MACHINE LEARNING CONTINUOUS IMPROVEMENT MODULE")
    print("="*80)
    
    # Initialize model
    ml_model = initialize_with_known_projects()
    
    # Test prediction on a new project
    print("\n\n--- TEST PREDICTION: Similar to Lynn ---")
    test_project = {
        'project_name': 'Test Project',
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
    
    print(f"\nProject: {test_project['project_name']}")
    print(f"Area: {test_project['area_sf']:,} SF")
    print(f"ML Prediction: ${prediction:,.0f} (${prediction/test_project['area_sf']:.2f}/SF)")
    print(f"Confidence: {metadata['confidence']}")
    
    # Compare with rule-based estimate
    rule_based = test_project['area_sf'] * 625  # Similar to Lynn
    print(f"Rule-Based: ${rule_based:,.0f} (${rule_based/test_project['area_sf']:.2f}/SF)")
    print(f"Difference: ${abs(prediction - rule_based):,.0f} ({abs(prediction - rule_based)/rule_based*100:.1f}%)")
    
    print("\n✅ ML module ready for continuous improvement!")
    print("   Add actual costs with: ml_model.update_with_actual(project_data, actual_cost)")


if __name__ == "__main__":
    main()
