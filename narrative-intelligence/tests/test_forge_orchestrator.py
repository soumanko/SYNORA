import pytest
from unittest.mock import MagicMock, patch
from agents.forge.orchestrator import ForgeOrchestrator
from agents.forge.generator import WritingIntent
from core.evaluation.quality_gate import QualityGate, QualityReport
from core.evaluation.intent_preservation import IntentPreservationResult

def _mock_dependencies():
    generator = MagicMock()
    generator.generate_initial_draft.return_value = {"draft_id": "draft_0", "content": "draft 0 text"}
    
    lens = MagicMock()
    prof = MagicMock()
    prof.dict.return_value = {"document_id": "fake_prof", "core30_features": {"document_id": "fake", "features": []}, "metadata": {}}
    lens.analyze_document.return_value = prof
    
    core30 = MagicMock()
    core30.core30_features = {}
    core30.analyze_deviation.return_value = []
    
    diag = MagicMock()
    diag.diagnose_deviations.return_value = []
    
    plan = MagicMock()
    plan.create_revision_plan.return_value = {"interventions": [{"op": "increase"}]}
    
    agent = MagicMock()
    agent.revise_draft.return_value = {"draft": "draft 1 text", "revision_summary": "sum"}
    
    effect = MagicMock()
    effect.evaluate.return_value = {"status": "success", "targets": [{"achievement": "achieved"}]}
    
    intent_pres = MagicMock()
    intent_pres.evaluate.return_value = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    
    qg = QualityGate()
    qg.evaluate = MagicMock(return_value=QualityReport(decision="continue", stop_reason=None, checks={}, blocking_issues=[], warnings=[]))
    
    return {
        "generator": generator,
        "lens_analyzer": lens,
        "core30_selector": core30,
        "diagnostic_engine": diag,
        "revision_planner": plan,
        "revision_agent": agent,
        "revision_effect_evaluator": effect,
        "intent_preservation_evaluator": intent_pres,
        "quality_gate": qg,
        "taxonomy": {}
    }

def test_orchestrator_max_cycles():
    deps = _mock_dependencies()
    # Force continue always so it hits max cycles
    deps["quality_gate"].evaluate.return_value = QualityReport(decision="continue", stop_reason=None, checks={}, blocking_issues=[], warnings=[])
    
    orch = ForgeOrchestrator(**deps)
    intent = WritingIntent(prompt="write", genre="a", tone="b", pov="c", length=10)
    state = orch.execute_run(intent, max_cycles=2)
    
    assert state.status == "stopped"
    assert state.stop_reason == "max_cycles_reached"
    # Draft 0 + Draft 1 + Draft 2 = 3 versions
    assert len(state.versions) == 3
    assert len(state.revisions) == 2

def test_orchestrator_stops_if_quality_gate_stops():
    deps = _mock_dependencies()
    deps["quality_gate"].evaluate.return_value = QualityReport(decision="stop", stop_reason="custom_stop", checks={}, blocking_issues=[], warnings=[])
    
    orch = ForgeOrchestrator(**deps)
    intent = WritingIntent(prompt="write", genre="a", tone="b", pov="c", length=10)
    state = orch.execute_run(intent, max_cycles=3)
    
    assert state.status == "stopped"
    assert state.stop_reason == "custom_stop"
    assert len(state.versions) == 2 # Draft 0 and Draft 1

def test_orchestrator_stops_if_no_actionable_targets():
    deps = _mock_dependencies()
    deps["revision_planner"].create_revision_plan.return_value = {"interventions": []}
    
    orch = ForgeOrchestrator(**deps)
    intent = WritingIntent(prompt="write", genre="a", tone="b", pov="c", length=10)
    state = orch.execute_run(intent, max_cycles=3)
    
    assert state.status == "stopped"
    assert state.stop_reason == "no_actionable_targets"
    assert len(state.versions) == 1 # Only draft 0

def test_orchestrator_stops_on_analysis_failure():
    deps = _mock_dependencies()
    deps["lens_analyzer"].analyze_document.side_effect = Exception("Lens failed")
    
    orch = ForgeOrchestrator(**deps)
    intent = WritingIntent(prompt="write", genre="a", tone="b", pov="c", length=10)
    state = orch.execute_run(intent, max_cycles=3)
    
    assert state.status == "stopped"
    assert state.stop_reason == "analysis_failed"
    assert len(state.versions) == 1
    assert state.versions[0].analysis_metadata["status"].startswith("analysis_failed")

def test_orchestrator_stops_on_revision_failure():
    deps = _mock_dependencies()
    deps["revision_agent"].revise_draft.side_effect = Exception("Agent failed")
    
    orch = ForgeOrchestrator(**deps)
    intent = WritingIntent(prompt="write", genre="a", tone="b", pov="c", length=10)
    state = orch.execute_run(intent, max_cycles=3)
    
    assert state.status == "stopped"
    assert "revision_failed" in state.stop_reason
    assert len(state.versions) == 1 # Preserves draft 0 safely
