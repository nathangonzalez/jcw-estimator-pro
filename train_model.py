"""
Training Script for ML Cost Estimator
======================================
Easy-to-use script for adding new projects and retraining the model
"""

from ml_continuous_improvement import CostEstimatorML

def add_new_project():
    """Interactive script to add a new project and retrain the model"""
    
    print("="*80)
    print(" ADD NEW PROJECT TO TRAINING DATA")
    print("="*80)
    
    # Load existing model
    ml_model = CostEstimatorML()
    
    # Get project details from user
    print("\nEnter project details:")
    
    project_data = {
        'project_name': input("Project name: "),
        'area_sf': float(input("Total area (SF): ")),
        'bedrooms': int(input("Number of bedrooms: ")),
        'bathrooms': int(input("Number of bathrooms: ")),
        'garage_bays': int(input("Number of garage bays: ")),
        'wall_height': float(input("Wall height (ft, default 10): ") or "10"),
        'perimeter_lf': float(input("Building perimeter (LF): ")),
        'roof_area_sf': float(input("Roof area (SF): ")),
        'windows': int(input("Number of windows: ")),
        'doors': int(input("Number of doors: ")),
        'finish_quality': input("Finish quality (economy/standard/premium/luxury): ").lower(),
        'design_complexity': input("Design complexity (simple/moderate/complex/luxury): ").lower(),
        'project_type': input("Project type (residential/commercial): ").lower(),
        'has_pool': input("Has pool? (y/n): ").lower() == 'y',
        'has_elevator': input("Has elevator? (y/n): ").lower() == 'y',
        'has_smart_home': input("Has smart home? (y/n): ").lower() == 'y',
        'stories': int(input("Number of stories (default 1): ") or "1"),
        'year': int(input("Year (default 2025): ") or "2025"),
        'actual_cost': float(input("Actual cost ($): "))
    }
    
    # Update model
    ml_model.update_with_actual(project_data, project_data['actual_cost'])
    
    print("\n✅ Model updated successfully!")
    print(f"   Total training projects: {len(ml_model.load_training_data())}")
    

def batch_add_projects():
    """Add multiple projects from a list"""
    
    print("="*80)
    print(" BATCH ADD PROJECTS")
    print("="*80)
    
    # Example: Add projects programmatically
    ml_model = CostEstimatorML()
    
    # Add your projects here
    new_projects = [
        # Example format - copy and modify:
        # {
        #     'project_name': 'Smith Residence',
        #     'area_sf': 4500,
        #     'bedrooms': 4,
        #     'bathrooms': 3,
        #     'garage_bays': 2,
        #     'wall_height': 10,
        #     'perimeter_lf': 270,
        #     'roof_area_sf': 4800,
        #     'windows': 28,
        #     'doors': 10,
        #     'finish_quality': 'premium',
        #     'design_complexity': 'moderate',
        #     'project_type': 'residential',
        #     'has_pool': False,
        #     'has_elevator': False,
        #     'has_smart_home': True,
        #     'stories': 1,
        #     'year': 2025,
        #     'actual_cost': 2800000
        # },
    ]
    
    if not new_projects:
        print("\n⚠️  No projects defined in batch_add_projects()")
        print("   Edit train_model.py and add project dictionaries to the new_projects list")
        return
    
    for project in new_projects:
        ml_model.update_with_actual(project, project['actual_cost'])
        print(f"✅ Added: {project['project_name']}")
    
    print(f"\n✅ Batch update complete!")
    print(f"   Total training projects: {len(ml_model.load_training_data())}")


def view_training_data():
    """View current training data"""
    
    print("="*80)
    print(" CURRENT TRAINING DATA")
    print("="*80)
    
    ml_model = CostEstimatorML()
    training_data = ml_model.load_training_data()
    
    print(f"\nTotal Projects: {len(training_data)}\n")
    
    for i, project in enumerate(training_data, 1):
        print(f"{i}. {project['project_name']}")
        print(f"   Area: {project['area_sf']:,.0f} SF")
        print(f"   Cost: ${project['actual_cost']:,.0f} (${project['actual_cost']/project['area_sf']:.2f}/SF)")
        print(f"   Quality: {project['finish_quality']} | Complexity: {project['design_complexity']}")
        print()


def test_prediction():
    """Test a prediction with the current model"""
    
    print("="*80)
    print(" TEST PREDICTION")
    print("="*80)
    
    ml_model = CostEstimatorML()
    
    # Example test project
    test_project = {
        'project_name': 'Test Prediction',
        'area_sf': float(input("\nArea (SF): ")),
        'bedrooms': int(input("Bedrooms: ")),
        'bathrooms': int(input("Bathrooms: ")),
        'garage_bays': int(input("Garage bays: ")),
        'wall_height': 10,
        'perimeter_lf': float(input("Perimeter (LF): ")),
        'roof_area_sf': float(input("Roof area (SF): ")),
        'windows': int(input("Windows: ")),
        'doors': int(input("Doors: ")),
        'finish_quality': input("Finish quality (economy/standard/premium/luxury): ").lower(),
        'design_complexity': input("Design complexity (simple/moderate/complex/luxury): ").lower(),
        'project_type': input("Project type (residential/commercial): ").lower(),
        'has_pool': input("Has pool? (y/n): ").lower() == 'y',
        'has_elevator': input("Has elevator? (y/n): ").lower() == 'y',
        'has_smart_home': input("Has smart home? (y/n): ").lower() == 'y',
        'stories': 1,
        'year': 2025
    }
    
    prediction, metadata = ml_model.predict(test_project)
    
    print(f"\n--- PREDICTION RESULTS ---")
    print(f"Project: {test_project['project_name']}")
    print(f"Area: {test_project['area_sf']:,.0f} SF")
    print(f"\nML Prediction: ${prediction:,.0f}")
    print(f"Cost per SF: ${prediction/test_project['area_sf']:.2f}/SF")
    print(f"Confidence: {metadata['confidence']}")


def main():
    """Main menu"""
    
    while True:
        print("\n" + "="*80)
        print(" ML COST ESTIMATOR - TRAINING MENU")
        print("="*80)
        print("\n1. Add single project (interactive)")
        print("2. Batch add projects (from code)")
        print("3. View training data")
        print("4. Test prediction")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            add_new_project()
        elif choice == '2':
            batch_add_projects()
        elif choice == '3':
            view_training_data()
        elif choice == '4':
            test_prediction()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n⚠️  Invalid option, please try again")


if __name__ == "__main__":
    main()
