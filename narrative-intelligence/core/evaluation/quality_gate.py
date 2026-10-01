from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from core.evaluation.intent_preservation import IntentPreservationResult
from agents.forge.generator import WritingIntent

class QualityCheck(BaseModel):
    status: str  # "pass", "fail", "unavailable", "requires_evaluation"
    details: str

class QualityReport(BaseModel):
    decision: str  # "continue", "stop"
    stop_reason: Optional[str]
    checks: Dict[str, QualityCheck]
    blocking_issues: List[str]
    warnings: List[str]

class QualityGate:
    """
    Evaluates the result of a revision cycle to determine if the Forge loop should continue.
    Does NOT fabricate qualitative judgments. Relies on observable constraints and measurements.
    """
    
    def evaluate(
        self, 
        intent: WritingIntent,
        intent_preservation: IntentPreservationResult, 
        revision_effect: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
        revision_plan: Dict[str, Any],
        cycle_number: int,
        max_cycles: int = 3
    ) -> QualityReport:
        
        checks = {}
        blocking_issues = []
        warnings = []
        
        # 1. Analysis Integrity
        analysis_status = analysis_metadata.get("status", "unknown")
        if analysis_status != "success":
            checks["analysis_integrity"] = QualityCheck(status="fail", details=f"Analysis failed: {analysis_status}")
            blocking_issues.append("Post-revision analysis failed or was incomplete.")
        else:
            checks["analysis_integrity"] = QualityCheck(status="pass", details="Analysis succeeded.")
            
        # 2. Intent Preservation (Hard Boundary)
        if intent_preservation.status == "fail":
            checks["intent_preservation"] = QualityCheck(status="fail", details=f"Failed intent checks: {intent_preservation.failed_checks}")
            blocking_issues.append("Revision violated explicitly required constraints.")
        else:
            checks["intent_preservation"] = QualityCheck(status="pass", details="All deterministic intent constraints preserved.")
            
        # Optional Intent checks breakdown for transparency
        checks["length"] = QualityCheck(
            status="pass" if intent_preservation.length_preserved else "fail",
            details="Length within bounds" if intent_preservation.length_preserved else "Length constraint violated."
        )
        checks["pov"] = QualityCheck(
            status="pass" if intent_preservation.pov_preserved else "fail",
            details="POV appears preserved." if intent_preservation.pov_preserved else "POV constraint violated."
        )
        
        # Semantic checks (unavailable deterministically)
        checks["genre"] = QualityCheck(status="requires_evaluation", details="Genre preservation requires human/evaluator review.")
        checks["tone"] = QualityCheck(status="requires_evaluation", details="Tone preservation requires human/evaluator review.")
        
        # 3. Target Achievement
        # Revision effect evaluation: {"status": "success", "targets": [...], "incidental_changes": [...]}
        achieved_targets = 0
        failed_targets = 0
        total_targets = 0
        
        if revision_effect.get("status") == "success":
            for target in revision_effect.get("targets", []):
                total_targets += 1
                if target.get("achievement") == "achieved":
                    achieved_targets += 1
                else:
                    failed_targets += 1
            
            checks["target_achievement"] = QualityCheck(
                status="pass" if achieved_targets == total_targets and total_targets > 0 else "fail",
                details=f"Achieved {achieved_targets}/{total_targets} targets."
            )
            
            # Incidental changes -> warnings
            incidental = revision_effect.get("incidental_changes", [])
            if incidental:
                warnings.append(f"Detected {len(incidental)} incidental changes to non-targeted features.")
        else:
            checks["target_achievement"] = QualityCheck(status="unavailable", details="Revision effect unavailable.")
            
        # Decision Logic
        if blocking_issues:
            decision = "stop"
            stop_reason = "intent_preservation_failed" if any("constraint" in i for i in blocking_issues) else "analysis_failed"
        elif total_targets > 0 and achieved_targets == total_targets:
            decision = "stop"
            stop_reason = "all_targets_achieved"
        elif not revision_plan.get("interventions"):
            decision = "stop"
            stop_reason = "no_actionable_targets"
        elif cycle_number >= max_cycles:
            decision = "stop"
            stop_reason = "max_cycles_reached"
        else:
            decision = "continue"
            stop_reason = None
            
        return QualityReport(
            decision=decision,
            stop_reason=stop_reason,
            checks=checks,
            blocking_issues=blocking_issues,
            warnings=warnings
        )
