import pytest
from core.taxonomy.taxonomy_loader import TaxonomyLoader
from core.extraction.dimension_analyzer import FeatureExtractor
from core.analysis.core30 import Core30Selector

def test_core_feature_integration():
    taxonomy_loader = TaxonomyLoader(
        taxonomy_path="data/storyscope/taxonomy.json",
        core30_path="data/storyscope/core30_approximation.json"
    )
    taxonomy = taxonomy_loader.load_taxonomy()
    core30_features = taxonomy_loader.load_core30()
    
    assert len(core30_features) == 30
    
    feature_extractor = FeatureExtractor(taxonomy, llm_provider=None)
    # Extract features - should return all 304 with value=None
    features = feature_extractor.extract_all("Test text")
    
    assert len(features) > 0, "FeatureExtractor returned zero features"
    
    core30_selector = Core30Selector(core30_features)
    core_features = core30_selector.filter_to_core(features)
    
    assert len(core_features) == 30, f"Expected 30 core features, got {len(core_features)}"
    
    feature_vector_ids = {f.feature_id for f in features}
    
    for feature in core_features:
        assert feature.feature_id in taxonomy, f"Feature {feature.feature_id} not in taxonomy"
        assert feature.feature_id in feature_vector_ids, f"Feature {feature.feature_id} not in FeatureVector"

