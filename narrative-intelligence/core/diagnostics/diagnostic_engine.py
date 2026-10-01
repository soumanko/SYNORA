from typing import List, Dict, Any
from pydantic import BaseModel
from core.taxonomy.schemas import FeatureValue

class DiagnosticRecommendation(BaseModel):
    target_feature: str
    current_value: Any
    diagnosis: str
    recommended_action: str
    priority: float
    preserve: List[str]

class DiagnosticEngine:
    """
    Analyzes feature deviations and produces targeted narrative interventions.
    """
    
    def __init__(self):
        pass
        
    def diagnose_deviations(self, deviations: List[Dict[str, Any]]) -> List[DiagnosticRecommendation]:
        """
        Translates raw feature deviations into actionable, narrative-level recommendations.
        Never recommends simply "making it more human".
        """
        recommendations = []
        for dev in deviations:
            if dev["deviation_score"] > 0.4:
                recommendations.append(
                    DiagnosticRecommendation(
                        target_feature=dev["feature_id"],
                        current_value=dev["value"],
                        diagnosis=f"Feature {dev['feature_id']} deviates significantly from expected genre norm.",
                        recommended_action=f"Adjust the narrative structure regarding {dev['feature_id']} to align better.",
                        priority=dev["importance"],
                        preserve=["tone", "POV", "plot", "character motivation"]
                    )
                )
        return sorted(recommendations, key=lambda x: x.priority, reverse=True)
