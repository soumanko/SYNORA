"""
Tests for RevisionEffectEvaluator.
Uses deterministic mocked profiles to verify type-aware comparison logic for operations.
"""

from core.evaluation.revision_effect import RevisionEffectEvaluator, FeatureChange
from core.analysis.narrative_profile import NarrativeProfile
from core.taxonomy.schemas import FeatureValue, FeatureVector, FeatureType, Feature, Dimension


def _make_profile(doc_id: str, features: list) -> NarrativeProfile:
    """Helper to build a NarrativeProfile from a list of FeatureValue dicts."""
    fvs = [FeatureValue(feature_id=f["id"], value=f["value"], confidence=f.get("confidence", 1.0)) for f in features]
    return NarrativeProfile(
        document_id=doc_id,
        core30_features=FeatureVector(document_id=doc_id, features=fvs),
        metadata={"analysis_mode": "core"}
    )


def _make_taxonomy():
    """Creates a minimal taxonomy for test features."""
    return {
        "F_SCALE_01": Feature(id="F_SCALE_01", name="Figurative Density", dimension=Dimension.STYLE, question="Q?", type=FeatureType.SCALE, values=["1","2","3","4","5"]),
        "F_CAT_01": Feature(id="F_CAT_01", name="Genre Category", dimension=Dimension.SITUATEDNESS, question="Q?", type=FeatureType.CATEGORICAL, values=["mystery","sci_fi","fantasy"]),
        "F_MULTI_01": Feature(id="F_MULTI_01", name="Thematic Domains", dimension=Dimension.PLOT, question="Q?", type=FeatureType.MULTI_SELECT, values=["love","power","survival"]),
        "F_ORD_01": Feature(id="F_ORD_01", name="Denouement Length", dimension=Dimension.PLOT, question="Q?", type=FeatureType.ORDINAL, values=["1","2","3"]),
        "F_BIN_01": Feature(id="F_BIN_01", name="Has Narrator", dimension=Dimension.PERSPECTIVE, question="Q?", type=FeatureType.BINARY, values=["yes","no"]),
    }


def test_scale_feature_increase_detected():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": 2}])
    profile_1 = _make_profile("d1", [{"id": "F_SCALE_01", "value": 4}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_SCALE_01"}, "operation": "increase"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    
    assert len(result["targeted_changes"]) == 1
    tc = result["targeted_changes"][0]
    assert tc["status"] == "measured"
    assert tc["delta"] == 2.0
    assert tc["direction_observed"] == "increase"
    assert tc["target_match"] == True


def test_scale_feature_decrease_detected():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": 5}])
    profile_1 = _make_profile("d1", [{"id": "F_SCALE_01", "value": 2}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_SCALE_01"}, "operation": "decrease"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    tc = result["targeted_changes"][0]
    assert tc["delta"] == -3.0
    assert tc["direction_observed"] == "decrease"
    assert tc["target_match"] == True


def test_unchanged_feature_detected():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": 3}, {"id": "F_BIN_01", "value": "yes"}])
    profile_1 = _make_profile("d1", [{"id": "F_SCALE_01", "value": 3}, {"id": "F_BIN_01", "value": "yes"}])
    
    plan = {"interventions": []}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    assert len(result["unchanged_features"]) == 2
    assert len(result["incidental_changes"]) == 0


def test_targeted_vs_incidental_separated():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [
        {"id": "F_SCALE_01", "value": 2},
        {"id": "F_CAT_01", "value": "mystery"},
    ])
    profile_1 = _make_profile("d1", [
        {"id": "F_SCALE_01", "value": 4},
        {"id": "F_CAT_01", "value": "sci_fi"},  # Changed but not targeted
    ])
    
    plan = {"interventions": [{"target": {"feature_id": "F_SCALE_01"}, "operation": "increase"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    assert len(result["targeted_changes"]) == 1
    assert result["targeted_changes"][0]["feature_id"] == "F_SCALE_01"
    assert len(result["incidental_changes"]) == 1
    assert result["incidental_changes"][0]["feature_id"] == "F_CAT_01"


def test_direction_mismatch_detected():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": 4}])
    profile_1 = _make_profile("d1", [{"id": "F_SCALE_01", "value": 2}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_SCALE_01"}, "operation": "increase"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    tc = result["targeted_changes"][0]
    assert tc["target_match"] == False  # Requested increase, got decrease


def test_missing_values_handled_safely():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": None}])
    profile_1 = _make_profile("d1", [{"id": "F_SCALE_01", "value": 3}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_SCALE_01"}, "operation": "increase"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    tc = result["targeted_changes"][0]
    assert tc["status"] == "unavailable"


def test_non_numeric_features_handled_safely():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    # Categorical: direction comparison should be unavailable
    profile_0 = _make_profile("d0", [{"id": "F_CAT_01", "value": "mystery"}])
    profile_1 = _make_profile("d1", [{"id": "F_CAT_01", "value": "sci_fi"}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_CAT_01"}, "operation": "increase"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    tc = result["targeted_changes"][0]
    assert tc["comparison_type"] == "categorical"
    assert tc["target_match"] == "comparison_unavailable"
    assert tc["changed"] == True


def test_multi_select_set_comparison():
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    profile_0 = _make_profile("d0", [{"id": "F_MULTI_01", "value": ["love", "power"]}])
    profile_1 = _make_profile("d1", [{"id": "F_MULTI_01", "value": ["love", "survival"]}])
    
    plan = {"interventions": [{"target": {"feature_id": "F_MULTI_01"}, "operation": "add", "target_value": "survival"}]}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    
    assert len(result["targeted_changes"]) == 1
    tc = result["targeted_changes"][0]
    assert tc["comparison_type"] == "set"
    assert "power" in tc["removed"]
    assert "survival" in tc["added"]
    assert "love" in tc["retained"]
    assert tc["target_match"] == True


def test_no_fabricated_measurements():
    """Verify evaluator does not invent values when features are absent."""
    taxonomy = _make_taxonomy()
    evaluator = RevisionEffectEvaluator(taxonomy)
    
    # Profile 0 has a feature, profile 1 does not
    profile_0 = _make_profile("d0", [{"id": "F_SCALE_01", "value": 3}])
    profile_1 = _make_profile("d1", [])
    
    plan = {"interventions": []}
    
    result = evaluator.evaluate(profile_0, profile_1, plan)
    # The feature should appear but with unavailable status since value_after is None
    found = [f for f in (result["incidental_changes"] + result["unchanged_features"]) if f["feature_id"] == "F_SCALE_01"]
    assert len(found) == 1
    assert found[0]["status"] == "unavailable"
