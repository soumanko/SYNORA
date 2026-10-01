from typing import List, Dict, Any, Optional
from core.diagnostics.diagnostic_engine import StructuredDiagnostic
from agents.forge.generator import WritingIntent
from core.taxonomy.schemas import FeatureType, Feature

class RevisionPlanner:
    """
    Orchestrates the Narrative Forge revision cycle based on diagnostics.
    Consumes StructuredDiagnostics and validates their operations.
    """
    
    def __init__(self, diagnostic_engine: Any = None, taxonomy: Dict[str, Feature] = None):
        self.diagnostic_engine = diagnostic_engine
        self.taxonomy = taxonomy or {}
        
    def _validate_operation(self, diag: StructuredDiagnostic, feature: Feature) -> bool:
        """
        Validates the proposed operation against taxonomy rules.
        """
        if diag.actionability != "actionable":
            return False
            
        op = diag.suggested_operation
        target = diag.suggested_target_value
        
        if op is None:
            return False
            
        if feature.type in (FeatureType.SCALE, FeatureType.ORDINAL):
            if op not in ("increase", "decrease"):
                return False
                
        elif feature.type in (FeatureType.CATEGORICAL, FeatureType.BINARY):
            if op != "set":
                return False
            if feature.values and str(target) not in [str(v) for v in feature.values]:
                return False
                
        elif feature.type == FeatureType.MULTI_SELECT:
            if op not in ("add", "remove"):
                return False
            if feature.values and str(target) not in [str(v) for v in feature.values]:
                return False
                
        return True

    def create_revision_plan(self, diagnostics: List[StructuredDiagnostic], intent: WritingIntent) -> Dict[str, Any]:
        """
        Selects a small number of meaningful targets (1-3) and formats them into a plan.
        Filters out invalid or informational diagnostics.
        """
        if not diagnostics:
            return {"status": "no_revision_needed", "interventions": []}
            
        interventions = []
        
        # Sort by priority
        priority_map = {"high": 3, "medium": 2, "low": 1}
        sorted_diags = sorted(diagnostics, key=lambda d: priority_map.get(d.priority, 0), reverse=True)
        
        for diag in sorted_diags:
            if len(interventions) >= 3:
                break
                
            fid = diag.feature_id
            if fid not in self.taxonomy:
                continue
                
            feature = self.taxonomy[fid]
            
            if not self._validate_operation(diag, feature):
                continue
                
            interventions.append({
                "target": {
                    "feature_id": feature.id,
                    "feature_name": feature.name,
                    "feature_type": feature.type.value if hasattr(feature.type, 'value') else str(feature.type)
                },
                "operation": diag.suggested_operation,
                "target_value": diag.suggested_target_value,
                "current_value": getattr(diag, 'current_value', None),
                "priority": diag.priority,
                "diagnostic_reason": diag.rationale,
                "revision_instruction": diag.observation,
                "constraints_to_preserve": [
                    "genre: " + intent.genre,
                    "tone: " + intent.tone,
                    "POV: " + intent.pov,
                    "required facts",
                    "plot"
                ] + (intent.constraints or [])
            })
            
        if not interventions:
            return {"status": "no_actionable_revision", "interventions": []}
            
        return {
            "status": "revision_planned",
            "interventions": interventions,
            "intent_constraints": {
                "prompt": intent.prompt,
                "genre": intent.genre,
                "tone": intent.tone,
                "pov": intent.pov,
                "length": intent.length,
                "constraints": intent.constraints
            }
        }
