import json
import glob
import os

def validate_models():
    models_dir = 'data/storyscope/models'
    model_files = glob.glob(os.path.join(models_dir, '*.json'))
    
    report = {}
    
    for mf in model_files:
        name = os.path.basename(mf)
        try:
            with open(mf, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            # XGBoost JSON format
            learner = model_data.get('learner', {})
            feature_names = learner.get('feature_names', [])
            num_features = learner.get('learner_model_param', {}).get('num_feature', "0")
            num_class = learner.get('learner_model_param', {}).get('num_class', "0")
            
            # Classes might not be explicitly named in XGBoost JSON, but let's just log what we have
            report[name] = {
                "status": "passed",
                "feature_count": len(feature_names) if feature_names else int(num_features),
                "num_class": int(num_class),
                "has_feature_names": bool(feature_names)
            }
        except Exception as e:
            report[name] = {
                "status": "failed",
                "reason": str(e)
            }
            
    with open('model_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    validate_models()
