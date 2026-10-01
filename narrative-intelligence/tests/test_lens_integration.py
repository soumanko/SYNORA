import pytest
from api.routes.lens import analyze_document, AnalyzeRequest, analyzer
from core.taxonomy.schemas import FeatureValue, EvidenceSpan
from core.extraction.dimension_analyzer import FeatureExtractor

def test_analyze_document_success():
    """
    Test that the analysis pipeline succeeds when extraction works.
    """
    # Mock the extractor to return values for the core 30 features
    class MockExtractor(FeatureExtractor):
        def extract_all(self, text: str):
            return [
                FeatureValue(
                    feature_id=f.id,
                    value="mock_value",
                    confidence=0.9,
                    evidence=[EvidenceSpan(text="mock evidence", start=0, end=10, reason="mock")]
                )
                for f in analyzer.core30_selector.core30_features.values()
            ]
            
    # Inject mock
    original_extractor = analyzer.feature_extractor
    analyzer.feature_extractor = MockExtractor(analyzer.feature_extractor.taxonomy, None)
    
    try:
        req = AnalyzeRequest(
            text="This is a short test document. The king died and then the queen died of grief.",
            document_id="doc-123"
        )
        
        response = analyze_document(req)
        
        assert response.status == "success"
        profile = response.narrative_profile
        assert profile is not None
        assert profile.full304_features is not None
        assert profile.core30_features is not None
        
        # Canonical field name
        assert hasattr(profile, "core30_features")
        
        assert len(profile.core30_features.features) == 30
        assert profile.metadata is not None
        
        # Verify evidence exists in at least one feature
        assert profile.core30_features.features[0].evidence is not None
        assert len(profile.core30_features.features[0].evidence) > 0
    finally:
        # Restore original
        analyzer.feature_extractor = original_extractor

def test_analyze_document_fails_cleanly():
    """
    Test that the analysis pipeline fails cleanly and returns a structured error
    when the core30 features are missing (e.g., if extraction produces zero features).
    """
    class EmptyExtractor(FeatureExtractor):
        def extract_all(self, text: str):
            return []
            
    original_extractor = analyzer.feature_extractor
    analyzer.feature_extractor = EmptyExtractor(analyzer.feature_extractor.taxonomy, None)
    
    try:
        req = AnalyzeRequest(
            text="This is a short test document. The king died and then the queen died of grief.",
            document_id="doc-123"
        )
        
        response = analyze_document(req)
    
        assert response.status == "failed"
        assert response.error is not None
        assert response.error.code == "CORE_FEATURE_ANALYSIS_FAILED"
        assert "no core30 features extracted" in response.error.message.lower()
        assert response.narrative_profile is None
    finally:
        analyzer.feature_extractor = original_extractor
