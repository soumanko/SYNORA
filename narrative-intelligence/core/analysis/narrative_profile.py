from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from core.taxonomy.schemas import FeatureVector, ClassifierResult, Core30Feature

class NarrativeProfile(BaseModel):
    """
    The unified artifact representing the comprehensive narrative analysis of a document.
    Consumed by both Narrative Forge and Narrative Lens.
    """
    document_id: str
    core30_features: FeatureVector
    full304_features: Optional[FeatureVector] = None
    classification: Optional[ClassifierResult] = None
    diagnostics: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    
    def get_dimension_scores(self) -> Dict[str, float]:
        """
        Aggregates individual features into interpretable dimension-level scores.
        """
        # Placeholder logic
        return {
            "Agents": 0.8,
            "Plot": 0.6,
            "Style": 0.7
        }
