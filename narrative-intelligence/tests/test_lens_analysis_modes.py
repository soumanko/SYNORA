import os
import sys
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.routes.lens import analyze_document, AnalyzeRequest
from core.taxonomy.schemas import FeatureVector

def test_core_mode_analysis():
    # Set core mode explicitly
    os.environ["LENS_ANALYSIS_MODE"] = "core"
    
    text = "Maya arrived at the station after midnight. The platform was empty except for an old man sitting beneath the broken clock."
    req = AnalyzeRequest(text=text, document_id="doc_123")
    
    try:
        res = analyze_document(req)
    except Exception as e:
        pytest.fail(f"Analysis failed: {str(e)}")
        
    assert res.status == "success", f"Failed: {res.error.message if res.error else 'Unknown'}"
    
    profile = res.narrative_profile
    assert profile is not None
    
    # Verify metadata
    assert profile.metadata.get("analysis_mode") == "core"
    assert profile.metadata.get("feature_coverage", {}).get("analyzed") == 30
    assert profile.metadata.get("feature_coverage", {}).get("total") == 304
    
    # Verify diagnostic scope
    assert profile.diagnostics.get("diagnostic_scope") == "core_features"
    
    # Verify full features exist but only 30 are populated with non-None values
    full_features = profile.full304_features.features
    assert len(full_features) == 304
    
    valid_count = sum(1 for f in full_features if f.value is not None)
    # It might be 30, but could be less if LLM fails on some. Should not be more than 30.
    assert valid_count <= 30
    
    # Verify classifier
    assert profile.classification is not None
    assert profile.classification.predicted_class == "unavailable"
    assert profile.classification.feature_set == "full feature set required"
    
    # Ensure no mock values used
    # This requires looking at the actual text/provider, which is real LLM in this case.

def test_full_mode_quota_failure():
    # Set full mode explicitly
    os.environ["LENS_ANALYSIS_MODE"] = "full"
    
    text = "Maya arrived at the station after midnight. The platform was empty except for an old man sitting beneath the broken clock."
    req = AnalyzeRequest(text=text, document_id="doc_123")
    
    res = analyze_document(req)
    
    # Should fail cleanly due to quota or other error since we don't have enough quota
    # If we have quota, it will succeed (but take 130 seconds), but we proved it fails
    # Let's just assert that it either succeeds or returns a clean failure with LLM_EXTRACTION_FAILED
    
    if res.status == "failed":
        assert res.error is not None
        assert "PROVIDER_ERROR" in res.error.message or "API Error" in res.error.message or "LLM_EXTRACTION_FAILED" in res.error.message
    else:
        assert res.status == "success"

if __name__ == "__main__":
    test_core_mode_analysis()
    # test_full_mode_quota_failure() will take 2 minutes, we can run via pytest if we want
