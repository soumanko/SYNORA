import json
from pathlib import Path
from typing import Dict, List
from .schemas import Feature, Core30Feature

class TaxonomyLoader:
    """Loads and validates the StoryScope taxonomy artifacts."""
    
    def __init__(self, taxonomy_path: str, core30_path: str = None):
        self.taxonomy_path = Path(taxonomy_path)
        self.core30_path = Path(core30_path) if core30_path else None
        self.features: Dict[str, Feature] = {}
        self.core30: List[Core30Feature] = []

    def load_taxonomy(self) -> Dict[str, Feature]:
        """Loads the full 304 feature taxonomy."""
        if not self.taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {self.taxonomy_path}")
            
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        feature_taxonomy = data.get("feature_taxonomy", {})
        for dim_key, dim_data in feature_taxonomy.items():
            dimension_name = dim_data.get("dimension_name")
            aspects = dim_data.get("aspects", {})
            for aspect_key, aspect_data in aspects.items():
                for feature_data in aspect_data.get("features", []):
                    # Inject dimension if missing
                    if "dimension" not in feature_data:
                        feature_data["dimension"] = dimension_name
                    
                    if feature_data.get("type") == "multi_select":
                        feature_data["type"] = "multi-select"
                        
                    feature = Feature(**feature_data)
                    self.features[feature.id] = feature
            
        return self.features

    def load_core30(self) -> List[Core30Feature]:
        """Loads the Core 30 features list."""
        if not self.core30_path or not self.core30_path.exists():
            raise FileNotFoundError(f"Core30 file not found: {self.core30_path}")
            
        with open(self.core30_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for feature_data in data.get("features", []):
            core_feature = Core30Feature(**feature_data)
            self.core30.append(core_feature)
            
        return self.core30
