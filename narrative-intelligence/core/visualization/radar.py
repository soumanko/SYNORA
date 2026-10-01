from typing import Dict, Any
from core.analysis.narrative_profile import NarrativeProfile

class RadarChartGenerator:
    """Generates a 10-dimension radar chart visualization for the frontend."""
    
    @staticmethod
    def generate(profile: NarrativeProfile) -> Dict[str, Any]:
        """
        Converts the NarrativeProfile dimension scores into a plottable radar format.
        """
        scores = profile.get_dimension_scores()
        
        return {
            "type": "radar",
            "labels": list(scores.keys()),
            "datasets": [
                {
                    "label": "Current Document",
                    "data": list(scores.values())
                },
                {
                    "label": "Human Reference",
                    "data": [0.75, 0.65, 0.8, 0.7, 0.6, 0.5, 0.8, 0.9, 0.6, 0.7] # Mock reference
                }
            ]
        }
