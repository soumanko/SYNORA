"""
Tests for IntentPreservationEvaluator.
Uses deterministic text samples to verify each check type.
"""

from core.evaluation.intent_preservation import IntentPreservationEvaluator
from agents.forge.generator import WritingIntent


def _make_intent(**kwargs):
    defaults = {
        "prompt": "Write a mystery scene.",
        "genre": "Mystery",
        "tone": "Suspenseful",
        "pov": "Third-person limited",
        "length": 200,
        "constraints": []
    }
    defaults.update(kwargs)
    return WritingIntent(**defaults)


def test_pov_third_person_preserved():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(pov="Third-person limited")
    
    draft_0 = "She walked into the room. Her eyes scanned the shelves."
    draft_1 = "She entered the library. Her gaze swept across the dusty volumes."
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["pov"]["status"] == "preserved"


def test_pov_first_person_preserved():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(pov="First person")
    
    draft_0 = "I walked into the room. My eyes scanned the shelves."
    draft_1 = "I entered the library. My gaze swept across the dusty volumes."
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["pov"]["status"] == "preserved"


def test_pov_possibly_changed():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(pov="First person")
    
    draft_0 = "I walked into the room. My eyes scanned the shelves."
    draft_1 = "The room was empty. Nothing stirred in the darkness."  # No first-person pronouns
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["pov"]["status"] == "possibly_changed"


def test_word_count_within_range():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(length=100)
    
    draft_0 = "Word " * 100
    draft_1 = "Word " * 110  # Within 30% tolerance
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["word_count"]["status"] == "within_range"
    assert result.details["word_count"]["method"] == "deterministic"


def test_word_count_out_of_range():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(length=100)
    
    draft_0 = "Word " * 100
    draft_1 = "Word " * 200  # Way outside 30% tolerance
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["word_count"]["status"] == "out_of_range"


def test_named_entity_preservation():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent()
    
    draft_0 = "Detective Morgan entered. Sarah was sitting by the window. The London fog crept in."
    draft_1 = "Detective Morgan arrived. Sarah sat near the window. The London mist rolled through."
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    assert result.details["named_entities"]["status"] == "checked"
    preserved = result.details["named_entities"]["preserved_in_draft_1"]
    assert "Morgan" in preserved
    assert "Sarah" in preserved
    assert "London" in preserved


def test_named_entity_missing():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent()
    
    draft_0 = "Detective Morgan entered. Sarah was sitting by the window."
    draft_1 = "The detective entered. A woman sat by the window."  # Names gone
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    missing = result.details["named_entities"]["missing_from_draft_1"]
    assert "Morgan" in missing
    assert "Sarah" in missing


def test_constraint_keyword_found():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(constraints=["Must include a dragon"])
    
    draft_0 = "The dragon flew overhead."
    draft_1 = "A massive dragon soared above the castle."
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    checks = result.details["constraints"]["checks"]
    assert len(checks) == 1
    assert checks[0]["keyword_presence"] == "found"


def test_constraint_keyword_missing():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(constraints=["Must include a dragon"])
    
    draft_0 = "The dragon flew overhead."
    draft_1 = "A massive bird soared above the castle."  # No dragon
    
    result = evaluator.evaluate(intent, draft_0, draft_1)
    checks = result.details["constraints"]["checks"]
    assert checks[0]["keyword_presence"] == "not_found"


def test_semantic_checks_marked_unavailable():
    """Tone and plot consistency should be explicitly marked as requiring evaluation."""
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent()
    
    result = evaluator.evaluate(intent, "Some text.", "Some other text.")
    
    assert result.details["tone"]["status"] == "requires_evaluation"
    assert result.details["semantic_plot_consistency"]["status"] == "requires_evaluation"
    assert result.details["genre"]["status"] == "requires_evaluation"


def test_no_constraints_specified():
    evaluator = IntentPreservationEvaluator()
    intent = _make_intent(constraints=[])
    
    result = evaluator.evaluate(intent, "Draft.", "Revised draft.")
    assert result.details["constraints"]["status"] == "no_constraints_specified"
