from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from agents.forge.generator import NarrativeForgeGenerator, WritingIntent
from agents.forge.revision_planner import RevisionPlanner
from agents.forge.revision_agent import RevisionAgent
from core.diagnostics.diagnostic_engine import DiagnosticEngine
from core.evaluation.revision_effect import RevisionEffectEvaluator
from core.evaluation.intent_preservation import IntentPreservationEvaluator
from core.evaluation.quality_gate import QualityGate
from agents.lens.analyzer import NarrativeLensAnalyzer
from core.analysis.core30 import Core30Selector
from core.taxonomy.schemas import Feature

class RevisionRecord(BaseModel):
    revision_number: int
    plan: Dict[str, Any]
    effect: Dict[str, Any]
    intent_preservation: Dict[str, Any]
    quality_report: Dict[str, Any]

class VersionRecord(BaseModel):
    version: str
    content: str
    narrative_profile: Optional[Dict[str, Any]]
    diagnostics: List[Dict[str, Any]]
    analysis_metadata: Dict[str, Any]

class ForgeRunState(BaseModel):
    run_id: str
    request: Dict[str, Any]
    versions: List[VersionRecord]
    revisions: List[RevisionRecord]
    current_version: str
    status: str
    stop_reason: Optional[str]
    metadata: Dict[str, Any]

class ForgeOrchestrator:
    """
    Coordinates the multi-cycle Narrative Forge loop.
    Enforces maximum cycles and utilizes the QualityGate for stopping conditions.
    """
    
    def __init__(
        self,
        generator: NarrativeForgeGenerator,
        lens_analyzer: NarrativeLensAnalyzer,
        core30_selector: Core30Selector,
        diagnostic_engine: DiagnosticEngine,
        revision_planner: RevisionPlanner,
        revision_agent: RevisionAgent,
        revision_effect_evaluator: RevisionEffectEvaluator,
        intent_preservation_evaluator: IntentPreservationEvaluator,
        quality_gate: QualityGate,
        taxonomy: Dict[str, Feature]
    ):
        self.generator = generator
        self.lens_analyzer = lens_analyzer
        self.core30_selector = core30_selector
        self.diagnostic_engine = diagnostic_engine
        self.revision_planner = revision_planner
        self.revision_agent = revision_agent
        self.revision_effect_evaluator = revision_effect_evaluator
        self.intent_preservation_evaluator = intent_preservation_evaluator
        self.quality_gate = quality_gate
        self.taxonomy = taxonomy
        self.reference_profile = {fid: "Expected Norm" for fid in self.core30_selector.core30_features.keys()}

    def _analyze_and_diagnose(self, content: str, version_id: str) -> tuple[Optional[Dict], List[Dict], Dict]:
        try:
            profile = self.lens_analyzer.analyze_document(document_id=version_id, document_text=content)
            deviations = self.core30_selector.analyze_deviation(profile.core30_features.features, self.reference_profile)
            diagnostics = self.diagnostic_engine.diagnose_deviations(deviations)
            return profile.dict(), [d.dict() for d in diagnostics], {"status": "success"}
        except Exception as e:
            return None, [], {"status": f"analysis_failed: {str(e)}"}

    def execute_run(self, intent: WritingIntent, max_cycles: int = 3, run_id: str = "run_0") -> ForgeRunState:
        # State Initialization
        state = ForgeRunState(
            run_id=run_id,
            request=vars(intent),
            versions=[],
            revisions=[],
            current_version="draft_0",
            status="running",
            stop_reason=None,
            metadata={}
        )

        # Cycle 0: Generation
        draft_0_result = self.generator.generate_initial_draft(intent)
        content_0 = draft_0_result["content"]
        
        prof_0, diags_0, meta_0 = self._analyze_and_diagnose(content_0, "draft_0")
        
        state.versions.append(VersionRecord(
            version="draft_0",
            content=content_0,
            narrative_profile=prof_0,
            diagnostics=diags_0,
            analysis_metadata=meta_0
        ))

        if meta_0["status"] != "success" or prof_0 is None:
            state.status = "stopped"
            state.stop_reason = "analysis_failed"
            return state

        current_content = content_0
        current_profile = prof_0
        current_diags = diags_0

        # Optimization Loop
        for cycle in range(1, max_cycles + 1):
            # 1. Plan
            from core.diagnostics.diagnostic_engine import StructuredDiagnostic
            sd_diags = [StructuredDiagnostic(**d) for d in current_diags]
            plan = self.revision_planner.create_revision_plan(sd_diags, intent)
            
            if not plan.get("interventions"):
                state.status = "stopped"
                state.stop_reason = "no_actionable_targets"
                break
                
            # 2. Revise
            try:
                from core.analysis.narrative_profile import NarrativeProfile
                # Convert prof_0 dict back to NarrativeProfile if needed, but revision_agent usually just uses it for reference
                # We'll pass current_profile as is if it accepts dict, or reconstruct.
                # Currently RevisionAgent doesn't strictly depend on the profile types to be instantiated beyond dict in the prompt.
                # However, for safety, let's reconstruct it if needed by revision_agent
                
                draft_result = self.revision_agent.revise_draft(intent, current_content, current_profile, current_diags, plan)
                new_content = draft_result["draft"]
            except Exception as e:
                state.status = "stopped"
                state.stop_reason = f"revision_failed: {str(e)}"
                break
                
            # 3. Analyze Revision
            version_id = f"draft_{cycle}"
            prof_n, diags_n, meta_n = self._analyze_and_diagnose(new_content, version_id)
            
            state.versions.append(VersionRecord(
                version=version_id,
                content=new_content,
                narrative_profile=prof_n,
                diagnostics=diags_n,
                analysis_metadata=meta_n
            ))
            
            if meta_n["status"] != "success" or current_profile is None or prof_n is None:
                state.status = "stopped"
                state.stop_reason = "analysis_failed"
                break
                
            # 4. Evaluate Revision Effect & Intent
            from core.analysis.narrative_profile import NarrativeProfile
            np_old = NarrativeProfile(**current_profile)
            np_new = NarrativeProfile(**prof_n)
            
            effect = self.revision_effect_evaluator.evaluate(np_old, np_new, plan)
            intent_pres = self.intent_preservation_evaluator.evaluate(intent, current_content, new_content)
            
            # 5. Quality Gate
            qg_report = self.quality_gate.evaluate(
                intent=intent,
                intent_preservation=intent_pres,
                revision_effect=effect,
                analysis_metadata=meta_n,
                revision_plan=plan,
                cycle_number=cycle,
                max_cycles=max_cycles
            )
            
            state.revisions.append(RevisionRecord(
                revision_number=cycle,
                plan=plan,
                effect=effect,
                intent_preservation=intent_pres.dict(),
                quality_report=qg_report.dict()
            ))
            
            state.current_version = version_id
            
            if qg_report.decision == "stop":
                state.status = "stopped"
                state.stop_reason = qg_report.stop_reason
                break
                
            # Prepare for next cycle
            current_content = new_content
            current_profile = prof_n
            current_diags = diags_n
            
            if cycle == max_cycles:
                state.status = "stopped"
                state.stop_reason = "max_cycles_reached"

        if state.status == "running":
            state.status = "completed"
            
        return state
