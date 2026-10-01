import json
from collections import defaultdict
from pathlib import Path

def approximate_core30():
    print("Loading taxonomy...")
    with open("data/storyscope/taxonomy.json", "r", encoding="utf-8") as f:
        taxonomy_data = json.load(f)
        
    feature_taxonomy = taxonomy_data.get('feature_taxonomy', {})
    
    # Build taxonomy mapping
    taxonomy = {}
    for dim_key, dim_data in feature_taxonomy.items():
        dim_name = dim_data.get("dimension_name", dim_key)
        for aspect_key, aspect_data in dim_data.get("aspects", {}).items():
            for f in aspect_data.get("features", []):
                fid = f.get('id')
                taxonomy[fid] = {
                    "id": fid,
                    "dimension": dim_name,
                    "name": f.get("name", fid)
                }
                
    print("Loading model...")
    with open("data/storyscope/models/binary_full.json", "r", encoding="utf-8") as f:
        model_data = json.load(f)
        
    feature_names = model_data.get("learner", {}).get("feature_names", [])
    if not feature_names:
        print("No feature names found in model.")
        return
        
    trees = model_data.get("learner", {}).get("gradient_booster", {}).get("model", {}).get("trees", [])
    
    # Count feature split frequency as a proxy for importance
    freq = defaultdict(int)
    for tree in trees:
        split_indices = tree.get("split_indices", [])
        for idx in split_indices:
            if idx < len(feature_names):
                col_name = feature_names[idx]
                # Map to taxonomy ID
                for fid in taxonomy:
                    if col_name == fid or col_name.startswith(fid + "_"):
                        freq[fid] += 1
                        break
                        
    # Sort and pick top 30
    sorted_features = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_30 = sorted_features[:30]
    
    features_out = []
    for rank, (fid, count) in enumerate(top_30, 1):
        features_out.append({
            "id": fid,
            "rank": rank,
            "importance": count,
            "stability": 0.0, # Approximation cannot compute bootstrap stability
            "dimension": taxonomy[fid]["dimension"],
            "name": taxonomy[fid]["name"]
        })
        
    core30_doc = {
        "version": "storyscope-core30-approximation-v1",
        "k": 30,
        "method": "XGBoost split-frequency approximation. This is not equivalent to the StoryScope SHAP analysis.",
        "source_commit": "main",
        "source_model": "binary_full.json",
        "dataset": "binary_full.json",
        "seed": 42,
        "features": features_out
    }
    
    out_path = Path("data/storyscope/core30_approximation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(core30_doc, f, indent=2)
        
    print(f"Approximated Core30 saved to {out_path} with {len(features_out)} features.")

if __name__ == "__main__":
    approximate_core30()
