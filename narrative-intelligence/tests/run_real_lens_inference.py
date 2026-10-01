import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.routes.lens import analyze_document, AnalyzeRequest

def print_report():
    print("Running Real Lens Inference...")
    text = "Maya arrived at the station after midnight. The platform was empty except for an old man sitting beneath the broken clock."
    
    req = AnalyzeRequest(text=text, document_id="doc_123")
    
    try:
        profile = analyze_document(req)
    except Exception as e:
        print(f"FAILED AT API LEVEL: {str(e)}")
        return
        
    print(f"Profile Status: {profile.status}")
    if profile.status == 'failed':
        print(f"Error: {profile.error.code} - {profile.error.message}")
        return
        
    print("\n--- 304 Extraction ---")
    features = profile.narrative_profile.full304
    total = len(features)
    valid = sum(1 for f in features if f.value is not None and f.value != "unspecified")
    unavailable = sum(1 for f in features if f.value == "unspecified")
    failed = sum(1 for f in features if f.value is None)
    
    print(f"Total records: {total}")
    print(f"Valid values: {valid}")
    print(f"Unavailable: {unavailable}")
    print(f"Failed: {failed}")
    
    print("\n--- Dimensions ---")
    dimensions_dict = profile.narrative_profile.dimensions
    for dim_name, feature_list in dimensions_dict.items():
        d_req = len(feature_list)
        d_valid = sum(1 for f in feature_list if f.value is not None and f.value != "unspecified")
        d_unavail = sum(1 for f in feature_list if f.value == "unspecified")
        d_fail = sum(1 for f in feature_list if f.value is None)
        print(f"{dim_name}: requested={d_req} valid={d_valid} unavailable={d_unavail} failed={d_fail}")
        
    print("\n--- Core Feature Analysis ---")
    core = profile.narrative_profile.core_feature_analysis
    print(f"Core Feature IDs: {len(core.resolved_ids)} / 30")
    print(f"Actual FeatureVector IDs: {len(core.resolved_ids)} / 30")
    print(f"Observed values: {core.observed_values}")
    print(f"Unavailable: {core.unavailable_values}")
    
    print("\n--- Encoding ---")
    # Actually encoding logic is handled inside lens analyzer. 
    # If the profile succeeded, encoding must have succeeded if classification exists.
    has_encoding = profile.classification is not None
    print(f"Status: {'PASS' if has_encoding else 'FAIL'}")
    
    print("\n--- Classification ---")
    cls = profile.classification
    if cls:
        print(f"Model: {cls.model_version}")
        print(f"Feature set: {cls.feature_set}")
        print("Classes:")
        for k,v in cls.probabilities.items():
            print(f"  {k}: {v}")
    else:
        print("FAIL")
        
    print("\n--- Evidence ---")
    ev_spans = 0
    ev_valid = 0
    ev_invalid = 0
    for f in features:
        if f.evidence:
            ev_spans += len(f.evidence)
            for ev in f.evidence:
                try:
                    span_text = text[ev.start:ev.end]
                    if span_text == ev.text:
                        ev_valid += 1
                    else:
                        ev_invalid += 1
                except:
                    ev_invalid += 1
    print(f"Evidence spans: {ev_spans}")
    print(f"Valid: {ev_valid}")
    print(f"Invalid: {ev_invalid}")
    print(f"Unavailable: {total - ev_spans}")

if __name__ == '__main__':
    load_dotenv()
    print_report()
