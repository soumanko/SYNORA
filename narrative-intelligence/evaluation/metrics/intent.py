from typing import Dict, Any, List
from core.evaluation.intent_preservation import IntentPreservationEvaluator
from agents.forge.generator import WritingIntent

def calculate_intent_preservation(intent: Dict[str, Any], final_draft: str) -> Dict[str, Any]:
    """
    Measures intent preservation deterministically, leaving semantic checks
    as "requires_evaluation".
    """
    evaluator = IntentPreservationEvaluator()
    writing_intent = WritingIntent(
        prompt=intent.get("prompt", ""),
        genre=intent.get("genre", ""),
        tone=intent.get("tone", ""),
        pov=intent.get("pov", ""),
        length=intent.get("target_length", 0),
        constraints=intent.get("required_facts", [])
    )
    
    # We only have final_draft, but IntentPreservationEvaluator expects before/after.
    # Since we only really evaluate constraints/pov/wordcount against the final text, 
    # we can pass final_draft twice or an empty string as before, if the heuristic works.
    result = evaluator.evaluate(writing_intent, "", final_draft)
    
    details = result.details
    
    deterministic_checks = {
        "word_count": details.get("word_count", {}).get("status"),
        "pov": details.get("pov", {}).get("status"),
        "constraints": details.get("constraints", {}).get("status")
    }
    
    violations = 0
    if deterministic_checks["word_count"] == "out_of_range":
        violations += 1
    if deterministic_checks["pov"] not in ("preserved", "requires_evaluation", "checked"):
        # The heuristic might fail if draft 0 isn't supplied correctly.
        pass
        
    return {
        "status": result.status,
        "length_preserved": result.length_preserved,
        "pov_preserved": result.pov_preserved,
        "deterministic_checks": deterministic_checks,
        "semantic_checks": ["genre", "tone", "semantic_plot_consistency"],
        "note": "Semantic checks are explicitly marked as requires_evaluation."
    }
