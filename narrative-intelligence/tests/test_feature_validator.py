"""
Tests for FeatureValidator.
Uses the taxonomy as the sole source of truth — no hardcoded values.
Verifies that invalid free-text values cannot silently enter the pipeline.
"""

from core.extraction.feature_validator import FeatureValidator, ValidationResult
from core.taxonomy.schemas import Feature, FeatureType, FeatureValue, Dimension


def _make_taxonomy():
    """Creates a minimal test taxonomy with one feature of each type."""
    return {
        "F_CAT": Feature(
            id="F_CAT", name="Genre", dimension=Dimension.SITUATEDNESS,
            question="Q?", type=FeatureType.CATEGORICAL,
            values=["mystery_detective", "thriller_suspense", "fantasy", "romance"]
        ),
        "F_BIN": Feature(
            id="F_BIN", name="Has Narrator", dimension=Dimension.PERSPECTIVE,
            question="Q?", type=FeatureType.BINARY,
            values=["yes", "no"]
        ),
        "F_MULTI": Feature(
            id="F_MULTI", name="Thematic Domains", dimension=Dimension.PLOT,
            question="Q?", type=FeatureType.MULTI_SELECT,
            values=["survival/fear", "power/authority", "love/attachment", "identity/selfhood"]
        ),
        "F_SCALE": Feature(
            id="F_SCALE", name="Figurative Density", dimension=Dimension.STYLE,
            question="Q?", type=FeatureType.SCALE,
            values=["1", "2", "3", "4", "5"]
        ),
        "F_ORD": Feature(
            id="F_ORD", name="Denouement", dimension=Dimension.PLOT,
            question="Q?", type=FeatureType.ORDINAL,
            values=[
                "none_or_minimal (story ends immediately after climax)",
                "brief (a short scene or paragraph of aftermath)",
                "extended (multiple scenes/time jumps of aftermath/epilogue)"
            ]
        ),
    }


# --- CATEGORICAL ---

def test_valid_categorical_accepted():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_CAT", value="mystery_detective")
    result = v.validate_feature(fv)
    assert result.valid
    assert result.normalized_value == "mystery_detective"


def test_invalid_categorical_rejected():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_CAT", value="curious")
    result = v.validate_feature(fv)
    assert not result.valid
    assert result.normalized_value is None
    assert result.error == "value_not_in_taxonomy"
    assert result.raw_value == "curious"


def test_invalid_free_text_rejected():
    """The exact failure case from Phase 9: 'academic building' for SIT_GEN_001."""
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_CAT", value="academic building")
    result = v.validate_feature(fv)
    assert not result.valid
    assert result.normalized_value is None


# --- MULTI-SELECT ---

def test_valid_multi_select_accepted():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_MULTI", value=["survival/fear", "love/attachment"])
    result = v.validate_feature(fv)
    assert result.valid
    assert result.normalized_value == ["survival/fear", "love/attachment"]


def test_invalid_multi_select_item_removed():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_MULTI", value=["survival/fear", "bogus_value", "love/attachment"])
    result = v.validate_feature(fv)
    assert result.valid  # Partially valid
    assert result.normalized_value == ["survival/fear", "love/attachment"]
    assert "bogus_value" in result.invalid_items


def test_all_invalid_multi_select():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_MULTI", value=["exploring", "trapped"])
    result = v.validate_feature(fv)
    assert not result.valid
    assert result.normalized_value is None
    assert result.error == "all_values_invalid"


# --- SCALE ---

def test_valid_scale_accepted():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_SCALE", value=3)
    result = v.validate_feature(fv)
    assert result.valid
    assert result.normalized_value == 3.0


def test_out_of_range_scale_rejected():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_SCALE", value=7)
    result = v.validate_feature(fv)
    assert not result.valid
    assert "out_of_range" in result.error


def test_non_numeric_scale_rejected():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_SCALE", value="high")
    result = v.validate_feature(fv)
    assert not result.valid
    assert "not_numeric" in result.error


# --- ORDINAL ---

def test_valid_ordinal_accepted():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_ORD", value="brief (a short scene or paragraph of aftermath)")
    result = v.validate_feature(fv)
    assert result.valid


def test_invalid_ordinal_rejected():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_ORD", value="suspenseful")
    result = v.validate_feature(fv)
    assert not result.valid
    assert result.error == "value_not_in_taxonomy"


# --- BINARY ---

def test_valid_binary_accepted():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_BIN", value="yes")
    result = v.validate_feature(fv)
    assert result.valid


def test_invalid_binary_rejected():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_BIN", value="maybe")
    result = v.validate_feature(fv)
    assert not result.valid


# --- NULL / MISSING ---

def test_null_value_handled():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_CAT", value=None)
    result = v.validate_feature(fv)
    assert result.valid
    assert result.normalized_value is None


def test_na_value_handled():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    fv = FeatureValue(feature_id="F_CAT", value="n/a")
    result = v.validate_feature(fv)
    assert result.valid
    assert result.normalized_value is None


# --- TAXONOMY SOURCE OF TRUTH ---

def test_taxonomy_used_as_source_of_truth():
    """Verify the validator uses the loaded taxonomy, not hardcoded values."""
    # Create a custom taxonomy with different values
    custom_tax = {
        "CUSTOM_01": Feature(
            id="CUSTOM_01", name="Custom", dimension=Dimension.STYLE,
            question="Q?", type=FeatureType.CATEGORICAL,
            values=["alpha", "beta", "gamma"]
        )
    }
    v = FeatureValidator(custom_tax)
    
    # "alpha" is valid in this custom taxonomy
    assert v.validate_feature(FeatureValue(feature_id="CUSTOM_01", value="alpha")).valid
    # "mystery" is NOT valid in this custom taxonomy
    assert not v.validate_feature(FeatureValue(feature_id="CUSTOM_01", value="mystery")).valid


# --- VALIDATE_FEATURE_VECTOR ---

def test_validate_feature_vector():
    tax = _make_taxonomy()
    v = FeatureValidator(tax)
    
    fvs = [
        FeatureValue(feature_id="F_CAT", value="mystery_detective"),
        FeatureValue(feature_id="F_CAT", value="curious"),  # Will use same taxonomy entry
    ]
    # Need unique IDs, so let's use the full taxonomy
    fvs = [
        FeatureValue(feature_id="F_CAT", value="curious"),        # Invalid
        FeatureValue(feature_id="F_BIN", value="yes"),              # Valid
        FeatureValue(feature_id="F_MULTI", value=["survival/fear"]),# Valid
        FeatureValue(feature_id="F_SCALE", value=3),                # Valid
        FeatureValue(feature_id="F_ORD", value="random text"),      # Invalid
    ]
    
    validated, metadata = v.validate_feature_vector(fvs)
    
    stats = metadata["extraction_validation"]
    assert stats["valid_features"] == 3
    assert stats["invalid_features"] == 2
    assert stats["total_features_attempted"] == 5
    
    # Check that invalid values are set to None
    cat_result = [fv for fv in validated if fv.feature_id == "F_CAT"][0]
    assert cat_result.value is None
    assert cat_result.confidence == 0.0
    
    # Check that valid values are preserved
    bin_result = [fv for fv in validated if fv.feature_id == "F_BIN"][0]
    assert bin_result.value == "yes"


# --- INTEGRATION: INVALID VALUES CANNOT REACH ENCODER ---

def test_invalid_free_text_cannot_reach_feature_vector():
    """
    End-to-end: a mocked LLM response containing 'curious' for a categorical
    feature must not result in FeatureValue(value='curious') after validation.
    """
    import json
    from core.extraction.structured_output import StructuredOutputValidator
    
    features = [
        Feature(
            id="AGENT_ATTR_001", name="Intro Mode", dimension=Dimension.AGENTS,
            question="Q?", type=FeatureType.CATEGORICAL,
            values=[
                "external description (appearance/background summary)",
                "in-action event (we see them doing something significant)",
                "in-dialogue (they speak before being described)",
                "inner thought/monologue",
                "through others' reports or gossip"
            ]
        )
    ]
    
    # Simulate LLM returning invalid free-text
    raw_json = json.dumps({"AGENT_ATTR_001": "curious"})
    
    validated = StructuredOutputValidator.validate(raw_json, features)
    
    assert len(validated) == 1
    result = validated[0]
    assert result.feature_id == "AGENT_ATTR_001"
    assert result.value is None  # Must NOT be "curious"
    assert result.confidence == 0.0
