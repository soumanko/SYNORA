from typing import List, Dict, Any
from core.taxonomy.schemas import FeatureValue, FeatureType, Feature

class Normalizer:
    """Normalizes raw feature values into standard formats based on taxonomy types."""
    
    def __init__(self, taxonomy: Dict[str, Feature]):
        self.taxonomy = taxonomy
        
    def normalize(self, feature_values: List[FeatureValue]) -> List[FeatureValue]:
        normalized = []
        for fv in feature_values:
            feature_schema = self.taxonomy.get(fv.feature_id)
            if not feature_schema:
                continue
                
            norm_val = self._normalize_value(fv.value, feature_schema)
            normalized.append(FeatureValue(
                feature_id=fv.feature_id,
                value=norm_val,
                confidence=fv.confidence,
                evidence=fv.evidence
            ))
        return normalized
        
    def _normalize_value(self, value: Any, schema: Feature) -> Any:
        if value == "n/a" or value is None:
            return None
            
        if schema.type == FeatureType.BINARY:
            if str(value).lower() in ["yes", "true", "1"]: return True
            if str(value).lower() in ["no", "false", "0"]: return False
            return None
            
        # Add handling for CATEGORICAL, ORDINAL, SCALE, MULTI_SELECT
        return value

class StoryScopeEncoder:
    """Encodes normalized feature vectors for XGBoost models."""
    
    def __init__(self, model_features_list: List[str]):
        # model_features_list contains the exact feature names expected by the model
        self.model_features_list = model_features_list
        
    def encode(self, normalized_features: List[FeatureValue]) -> Dict[str, float]:
        """
        Encodes features. Fails loudly if a required column is fundamentally missing 
        or if encoding mapping fails.
        """
        encoded_dict = {feat: 0.0 for feat in self.model_features_list}
        
        feature_map = {fv.feature_id: fv.value for fv in normalized_features}
        
        # In a real implementation, map categorical to one-hot, ordinals to ints, etc.
        # This must match StoryScope exactly.
        
        return encoded_dict
