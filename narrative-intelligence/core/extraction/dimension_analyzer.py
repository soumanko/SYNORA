from typing import List, Dict, Any
from core.taxonomy.schemas import Dimension, FeatureValue, Feature, FeatureType

class DimensionAnalyzer:
    """
    Analyzes a specific narrative dimension using an LLM to extract features.
    Constructs taxonomy-constrained schemas so the LLM is prompted with valid value sets.
    """
    
    def __init__(self, dimension: Dimension, features: List[Feature], llm_provider: Any):
        self.dimension = dimension
        self.features = features
        self.llm_provider = llm_provider
        
    def _build_constrained_schema(self) -> Dict[str, Any]:
        """
        Builds a JSON schema that constrains extraction output to valid taxonomy values.
        Uses enum constraints for categorical/binary/ordinal, items.enum for multi-select,
        and numeric bounds for scale features.
        """
        schema = {}
        for f in self.features:
            allowed_values = [str(v) for v in f.values] if f.values else []
            
            if f.type == FeatureType.CATEGORICAL or f.type == FeatureType.BINARY:
                schema[f.id] = {
                    "type": "string",
                    "enum": allowed_values,
                    "description": f"{f.name}: {f.question}"
                }
            elif f.type == FeatureType.MULTI_SELECT:
                schema[f.id] = {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": allowed_values
                    },
                    "description": f"{f.name}: {f.question}. Select all that apply from the allowed values."
                }
            elif f.type == FeatureType.SCALE:
                # Extract numeric bounds
                try:
                    bounds = [float(str(v).strip().split(" ")[0]) for v in f.values]
                    min_val, max_val = int(min(bounds)), int(max(bounds))
                except (ValueError, TypeError):
                    min_val, max_val = 1, 5
                schema[f.id] = {
                    "type": "integer",
                    "minimum": min_val,
                    "maximum": max_val,
                    "description": f"{f.name}: {f.question}. Provide an integer from {min_val} to {max_val}."
                }
            elif f.type == FeatureType.ORDINAL:
                schema[f.id] = {
                    "type": "string",
                    "enum": allowed_values,
                    "description": f"{f.name}: {f.question}"
                }
            else:
                schema[f.id] = {
                    "type": "string",
                    "description": f"{f.name}: {f.question}"
                }
        return schema
        
    def analyze(self, text: str) -> List[FeatureValue]:
        """
        Analyzes the text for features belonging to this dimension.
        Constructs a taxonomy-constrained schema, validates output.
        """
        schema = self._build_constrained_schema()
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
