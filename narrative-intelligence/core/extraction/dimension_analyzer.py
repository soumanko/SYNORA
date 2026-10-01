from typing import List, Dict, Any
from core.taxonomy.schemas import Dimension, FeatureValue, Feature

class DimensionAnalyzer:
    """
    Analyzes a specific narrative dimension using an LLM to extract features.
    """
    
    def __init__(self, dimension: Dimension, features: List[Feature], llm_provider: Any):
        self.dimension = dimension
        self.features = features
        self.llm_provider = llm_provider
        
    def analyze(self, text: str) -> List[FeatureValue]:
        """
        Analyzes the text for features belonging to this dimension.
        Constructs a structured analysis prompt, validates output, and extracts evidence.
        """
        schema = {f.id: {"value": f.type, "confidence": 1.0, "evidence": [{"text": "snippet", "start": 0, "end": 1, "reason": "reason"}]} for f in self.features}
        try:
            raw_json = self.llm_provider.get_structured_output(text, schema)
            from core.extraction.structured_output import StructuredOutputValidator
            return StructuredOutputValidator.validate(raw_json, self.features)
        except Exception as e:
            if "LLM_PROVIDER_NOT_CONFIGURED" in str(e):
                raise ValueError("LLM_PROVIDER_NOT_CONFIGURED")
            if "API Error" in str(e) or "LLM_EXTRACTION_FAILED" in str(e):
                raise ValueError(f"PROVIDER_ERROR: {str(e)}")
            return [
                FeatureValue(feature_id=f.id, value=None, confidence=0.0)
                for f in self.features
            ]

class FeatureExtractor:
    """
    Coordinates extraction across all 10 dimensions to produce 304 feature values.
    """
    
    def __init__(self, taxonomy: Dict[str, Feature], llm_provider: Any):
        self.taxonomy = taxonomy
        self.llm_provider = llm_provider
        self.dimension_analyzers = self._initialize_analyzers()
        
    def _initialize_analyzers(self) -> Dict[Dimension, DimensionAnalyzer]:
        analyzers = {}
        features_by_dim = {}
        for feature in self.taxonomy.values():
            if feature.dimension not in features_by_dim:
                features_by_dim[feature.dimension] = []
            features_by_dim[feature.dimension].append(feature)
            
        for dim, feats in features_by_dim.items():
            analyzers[dim] = DimensionAnalyzer(dimension=dim, features=feats, llm_provider=self.llm_provider)
            
        return analyzers
    def extract_all(self, text: str) -> List[FeatureValue]:
        results = []
        import time
        for analyzer in self.dimension_analyzers.values():
            results.extend(analyzer.analyze(text))
            time.sleep(13) # Rate limit mitigation for free tier (5 req/min)
        return results
