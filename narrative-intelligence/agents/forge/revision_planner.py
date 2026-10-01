from typing import List, Any
from core.diagnostics.diagnostic_engine import DiagnosticRecommendation
from agents.forge.generator import WritingIntent

class RevisionPlanner:
    """
    Orchestrates the Narrative Forge revision cycle based on diagnostics.
    """
    
    def __init__(self, diagnostic_engine: Any):
        self.diagnostic_engine = diagnostic_engine
        
    def create_revision_plan(self, diagnostics: List[DiagnosticRecommendation], intent: WritingIntent) -> dict:
        """
        Selects the top priority interventions and formats them into a plan that 
        preserves the original user intent.
        """
        if not diagnostics:
            return {"status": "no_revision_needed"}
            
        top_interventions = diagnostics[:3] # Limit to top 3 fixes per cycle
        
        return {
            "status": "revision_planned",
            "interventions": top_interventions,
            "intent_constraints": {
                "genre": intent.genre,
                "tone": intent.tone,
                "pov": intent.pov
            }
        }
