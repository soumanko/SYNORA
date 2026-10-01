import pytest
from core.diagnostics.diagnostic_engine import DiagnosticEngine, StructuredDiagnostic
from core.taxonomy.schemas import Feature, FeatureType, Dimension

def _make_tax():
    return {
        "F_SCALE": Feature(id="F_SCALE", name="Scale", dimension=Dimension.PLOT, question="Q?", type=FeatureType.SCALE, values=["1", "2", "3", "4", "5"]),
        "F_CAT": Feature(id="F_CAT", name="Cat", dimension=Dimension.PLOT, question="Q?", type=FeatureType.CATEGORICAL, values=["a", "b"]),
        "F_MULTI": Feature(id="F_MULTI", name="Multi", dimension=Dimension.PLOT, question="Q?", type=FeatureType.MULTI_SELECT, values=["x", "y"]),
    }

def test_diagnostic_contains_real_feature_id():
    engine = DiagnosticEngine(_make_tax())
    diags = engine.diagnose_deviations([{"feature_id": "F_SCALE", "value": "1", "deviation_score": 0.9}])
    assert len(diags) == 1
    assert diags[0].feature_id == "F_SCALE"
    assert diags[0].feature_type == "scale"

def test_informational_diagnostic_has_no_revision_operation():
    # Since categorical isn't supported with LLM guessing yet in our basic heuristic, it defaults to informational.
    engine = DiagnosticEngine(_make_tax())
    diags = engine.diagnose_deviations([{"feature_id": "F_CAT", "value": "a", "deviation_score": 0.9}])
    assert diags[0].actionability == "informational"
    assert diags[0].suggested_operation is None

def test_scale_diagnostic_can_produce_increase():
    engine = DiagnosticEngine(_make_tax())
    diags = engine.diagnose_deviations([{"feature_id": "F_SCALE", "value": "1", "deviation_score": 0.9}])
    assert diags[0].actionability == "actionable"
    assert diags[0].suggested_operation == "increase"

def test_missing_evidence_remains_empty():
    engine = DiagnosticEngine(_make_tax())
    diags = engine.diagnose_deviations([{"feature_id": "F_SCALE", "value": "1", "deviation_score": 0.9}])
    assert diags[0].evidence == []

def test_no_fabricated_feature_ids():
    engine = DiagnosticEngine(_make_tax())
    diags = engine.diagnose_deviations([{"feature_id": "MADE_UP", "value": "1", "deviation_score": 0.9}])
    assert len(diags) == 0

def test_structured_diagnostic_schema():
    diag = StructuredDiagnostic(
        diagnostic_id="123",
        feature_id="F_SCALE",
        feature_name="Scale",
        feature_type="scale",
        current_value="1",
        observation="Test",
        rationale="Test",
        actionability="actionable",
        suggested_operation="increase",
        suggested_target_value=None,
        evidence=[{"text": "foo", "start": 0, "end": 3}],
        priority="high"
    )
    assert diag.feature_id == "F_SCALE"
    assert len(diag.evidence) == 1
