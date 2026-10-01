from typing import List, Dict, Any
from core.taxonomy.schemas import FeatureValue, Core30Feature

class Core30Selector:
    """
    Manages the Core 30 feature subset for fast-path analysis.
    Filters the full feature set down to the most important top 30 features.
    """
    
    def __init__(self, core30_features: List[Core30Feature]):
        self.core30_features = {f.id: f for f in core30_features}
        
    def filter_to_core(self, all_features: List[FeatureValue]) -> List[FeatureValue]:
        """
        Takes the full set of extracted features and returns only those in the Core30.
        """
        return [fv for fv in all_features if fv.feature_id in self.core30_features]
        
    def analyze_deviation(self, core_features: List[FeatureValue], reference_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compares the extracted Core30 features against a reference distribution (e.g., human baseline).
        Returns deviation metrics to guide the revision engine.
        """
        deviations = []
        for fv in core_features:
            ref_val = reference_profile.get(fv.feature_id)
            if ref_val is not None:
                # Basic deviation placeholder
                deviations.append({
                    "feature_id": fv.feature_id,
                    "value": fv.value,
                    "reference": ref_val,
                    "deviation_score": 0.5, # Example
                    "importance": self.core30_features[fv.feature_id].importance
                })
        return deviations
