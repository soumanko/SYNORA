import pytest
from agents.forge.revision_planner import RevisionPlanner
from core.diagnostics.diagnostic_engine import StructuredDiagnostic
from core.taxonomy.schemas import Feature, FeatureType, Dimension
from agents.forge.generator import WritingIntent


def _make_taxonomy():
    return {
        "SCALE_01": Feature(
            id="SCALE_01", name="Scale", dimension=Dimension.STYLE,
            question="Q?", type=FeatureType.SCALE, values=["1", "2", "3", "4", "5"]
        ),
        "ORD_01": Feature(
            id="ORD_01", name="Ordinal", dimension=Dimension.PLOT,
            question="Q?", type=FeatureType.ORDINAL, values=["low", "medium", "high"]
        ),
        "CAT_01": Feature(
            id="CAT_01", name="Categorical", dimension=Dimension.SITUATEDNESS,
            question="Q?", type=FeatureType.CATEGORICAL, values=["alpha", "beta", "gamma"]
        ),
        "MULTI_01": Feature(
            id="MULTI_01", name="Multi", dimension=Dimension.SETTING,
            question="Q?", type=FeatureType.MULTI_SELECT, values=["x", "y", "z"]
        )
    }

def _make_intent():
    return WritingIntent(prompt="write", genre="fiction", tone="dark", pov="first", length=200)

def test_scale_increase():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="SCALE_01",
            feature_name="Scale",
            feature_type="scale",
            current_value="1",
            observation="Too low",
            rationale="Needs increase",
            actionability="actionable",
            suggested_operation="increase",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "revision_planned"
    assert len(plan["interventions"]) == 1
    assert plan["interventions"][0]["operation"] == "increase"
    assert plan["interventions"][0]["target_value"] is None

def test_scale_decrease():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="SCALE_01",
            feature_name="Scale",
            feature_type="scale",
            current_value="5",
            observation="Too high",
            rationale="Needs decrease",
            actionability="actionable",
            suggested_operation="decrease",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["interventions"][0]["operation"] == "decrease"

def test_ordinal_directional():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="ORD_01",
            feature_name="Ordinal",
            feature_type="ordinal",
            current_value="low",
            observation="Too low",
            rationale="Needs increase",
            actionability="actionable",
            suggested_operation="increase",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["interventions"][0]["operation"] == "increase"

def test_categorical_set():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="CAT_01",
            feature_name="Categorical",
            feature_type="categorical",
            current_value="alpha",
            observation="Wrong category",
            rationale="Needs beta",
            actionability="actionable",
            suggested_operation="set",
            suggested_target_value="beta",
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["interventions"][0]["operation"] == "set"
    assert plan["interventions"][0]["target_value"] == "beta"

def test_multi_select_add():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="MULTI_01",
            feature_name="Multi",
            feature_type="multi_select",
            current_value=[],
            observation="Missing",
            rationale="Needs x",
            actionability="actionable",
            suggested_operation="add",
            suggested_target_value="x",
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["interventions"][0]["operation"] == "add"
    assert plan["interventions"][0]["target_value"] == "x"

def test_multi_select_remove():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="MULTI_01",
            feature_name="Multi",
            feature_type="multi_select",
            current_value=["x", "y"],
            observation="Extra",
            rationale="Needs removal",
            actionability="actionable",
            suggested_operation="remove",
            suggested_target_value="x",
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["interventions"][0]["operation"] == "remove"
    assert plan["interventions"][0]["target_value"] == "x"

def test_invalid_categorical_target_rejected():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="CAT_01",
            feature_name="Categorical",
            feature_type="categorical",
            current_value="alpha",
            observation="Wrong category",
            rationale="Needs omega",
            actionability="actionable",
            suggested_operation="set",
            suggested_target_value="omega", # Not in taxonomy
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "no_actionable_revision"

def test_invalid_multi_select_target_rejected():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="MULTI_01",
            feature_name="Multi",
            feature_type="multi_select",
            current_value=[],
            observation="Missing",
            rationale="Needs omega",
            actionability="actionable",
            suggested_operation="add",
            suggested_target_value="omega", # Not in taxonomy
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "no_actionable_revision"

def test_categorical_never_receives_increase_decrease():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="CAT_01",
            feature_name="Categorical",
            feature_type="categorical",
            current_value="alpha",
            observation="Wrong category",
            rationale="Needs increase",
            actionability="actionable",
            suggested_operation="increase", # Invalid op for cat
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "no_actionable_revision"

def test_unactionable_diagnostic_excluded():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="SCALE_01",
            feature_name="Scale",
            feature_type="scale",
            current_value="3",
            observation="Fine",
            rationale="Looks okay",
            actionability="informational",
            suggested_operation=None,
            suggested_target_value=None,
            evidence=[],
            priority="low"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "no_actionable_revision"

def test_maximum_3_active_targets():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(diagnostic_id=str(i), feature_id="SCALE_01", feature_name="Scale", feature_type="scale", current_value="1", observation="L", rationale="inc", actionability="actionable", suggested_operation="increase", suggested_target_value=None, evidence=[], priority="high")
        for i in range(4)
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert len(plan["interventions"]) == 3

def test_preservation_constraints_separate():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="SCALE_01",
            feature_name="Scale",
            feature_type="scale",
            current_value="1",
            observation="Too low",
            rationale="Needs increase",
            actionability="actionable",
            suggested_operation="increase",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    intervention = plan["interventions"][0]
    assert "genre: fiction" in intervention["constraints_to_preserve"]
    assert "tone: dark" in intervention["constraints_to_preserve"]

def test_no_invented_feature_ids():
    tax = _make_taxonomy()
    planner = RevisionPlanner(taxonomy=tax)
    diags = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="MADE_UP",
            feature_name="Made Up",
            feature_type="scale",
            current_value="1",
            observation="L",
            rationale="inc",
            actionability="actionable",
            suggested_operation="increase",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    plan = planner.create_revision_plan(diags, _make_intent())
    assert plan["status"] == "no_actionable_revision"

