import pytest
from core.evaluation.quality_gate import QualityGate
from core.evaluation.intent_preservation import IntentPreservationResult
from agents.forge.generator import WritingIntent

def _make_intent():
    return WritingIntent(prompt="write", genre="fiction", tone="dark", pov="first", length=100)

def test_intent_preservation_failure_stops():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="fail", length_preserved=True, pov_preserved=False, failed_checks=["pov"], details={})
    rep = gate.evaluate(intent, pres, {"status": "success"}, {"status": "success"}, {"interventions": [{"fake": 1}]}, 1)
    
    assert rep.decision == "stop"
    assert rep.stop_reason == "intent_preservation_failed"
    assert "intent_preservation" in rep.checks
    assert rep.checks["intent_preservation"].status == "fail"
    assert len(rep.blocking_issues) > 0

def test_analysis_failure_stops():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    rep = gate.evaluate(intent, pres, {"status": "success"}, {"status": "failed"}, {"interventions": [{"fake": 1}]}, 1)
    
    assert rep.decision == "stop"
    assert rep.stop_reason == "analysis_failed"

def test_no_actionable_targets_stops():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    # Empty interventions array
    rep = gate.evaluate(intent, pres, {"status": "success"}, {"status": "success"}, {"interventions": []}, 1)
    
    assert rep.decision == "stop"
    assert rep.stop_reason == "no_actionable_targets"

def test_all_targets_achieved_stops():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    
    # 2 targets, both achieved
    eff = {
        "status": "success",
        "targets": [
            {"achievement": "achieved"},
            {"achievement": "achieved"}
        ]
    }
    rep = gate.evaluate(intent, pres, eff, {"status": "success"}, {"interventions": [{"fake": 1}, {"fake": 2}]}, 1)
    
    assert rep.decision == "stop"
    assert rep.stop_reason == "all_targets_achieved"

def test_max_cycles_stops():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    eff = {
        "status": "success",
        "targets": [
            {"achievement": "failed"}
        ]
    }
    rep = gate.evaluate(intent, pres, eff, {"status": "success"}, {"interventions": [{"fake": 1}]}, 3, max_cycles=3)
    
    assert rep.decision == "stop"
    assert rep.stop_reason == "max_cycles_reached"

def test_continue_when_appropriate():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    eff = {
        "status": "success",
        "targets": [
            {"achievement": "failed"}  # Not all achieved
        ]
    }
    rep = gate.evaluate(intent, pres, eff, {"status": "success"}, {"interventions": [{"fake": 1}]}, 1, max_cycles=3)
    
    assert rep.decision == "continue"
    assert rep.stop_reason is None

def test_unavailable_semantic_checks():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    eff = {"status": "success", "targets": [{"achievement": "failed"}]}
    rep = gate.evaluate(intent, pres, eff, {"status": "success"}, {"interventions": [{"fake": 1}]}, 1)
    
    assert "genre" in rep.checks
    assert rep.checks["genre"].status == "requires_evaluation"
    assert "tone" in rep.checks
    assert rep.checks["tone"].status == "requires_evaluation"

def test_incidental_changes_add_warnings():
    gate = QualityGate()
    intent = _make_intent()
    pres = IntentPreservationResult(status="pass", length_preserved=True, pov_preserved=True, failed_checks=[], details={})
    eff = {
        "status": "success",
        "targets": [{"achievement": "failed"}],
        "incidental_changes": [{}, {}]
    }
    rep = gate.evaluate(intent, pres, eff, {"status": "success"}, {"interventions": [{"fake": 1}]}, 1)
    
    assert len(rep.warnings) > 0
    assert "2 incidental changes" in rep.warnings[0]
