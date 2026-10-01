import json
import sys

def validate():
    try:
        with open('data/storyscope/taxonomy.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"status": "failed", "reason": f"Could not load: {e}"}))
        sys.exit(1)

    feature_taxonomy = data.get('feature_taxonomy', {})
    
    feature_count = 0
    dimensions = set()
    feature_ids = set()
    duplicate_ids = []
    invalid_features = []
    valid_types = {"binary", "categorical", "ordinal", "scale", "multi_select"}
    
    for dim_key, dim_data in feature_taxonomy.items():
        dim_name = dim_data.get("dimension_name", dim_key)
        dimensions.add(dim_name)
        
        for aspect_key, aspect_data in dim_data.get("aspects", {}).items():
            for f in aspect_data.get("features", []):
                feature_count += 1
                fid = f.get('id')
                if fid in feature_ids:
                    duplicate_ids.append(fid)
                feature_ids.add(fid)
                
                ftype = f.get('type')
                if ftype not in valid_types:
                    invalid_features.append(fid)
            
    status = "passed"
    if feature_count != 304 or len(dimensions) != 10 or duplicate_ids or invalid_features:
        status = "failed"
        
    report = {
        "status": status,
        "feature_count": feature_count,
        "dimension_count": len(dimensions),
        "duplicate_ids": duplicate_ids,
        "invalid_features": invalid_features
    }
    
    with open('taxonomy_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    validate()
