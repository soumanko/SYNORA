"""
IntentPreservationEvaluator: Deterministic checks for whether user intent 
was preserved through the revision cycle.

Uses deterministic checks where possible (genre, POV, word count).
Clearly marks semantic checks (plot consistency, factual preservation)
as requiring qualitative/LLM evaluation rather than fabricating scores.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from agents.forge.generator import WritingIntent

class IntentPreservationResult(BaseModel):
    status: str
    length_preserved: bool
    pov_preserved: bool
    failed_checks: List[str]
    details: Dict[str, Any]

class IntentPreservationEvaluator:
    """
    Evaluates whether user intent was preserved through a revision.
    
    Deterministic checks:
      - genre keyword in text (heuristic)
      - POV pronoun patterns
      - word count within range
      - named entity preservation
      - required fact presence
    
    Explicitly unavailable (marked as such):
      - semantic plot consistency
      - tonal consistency (requires LLM)
    """
    
    # POV detection heuristics: maps POV label to expected pronoun patterns
    POV_PATTERNS = {
        "first person": {"I ", "I'", " me ", " my ", " mine "},
        "first-person": {"I ", "I'", " me ", " my ", " mine "},
        "second person": {"You ", " you ", " your ", " yours "},
        "second-person": {"You ", " you ", " your ", " yours "},
        "third person": {" he ", " she ", " they ", " his ", " her ", " their "},
        "third-person": {" he ", " she ", " they ", " his ", " her ", " their "},
        "third-person limited": {" he ", " she ", " they ", " his ", " her ", " their "},
        "third-person omniscient": {" he ", " she ", " they ", " his ", " her ", " their "},
    }
    
    # Reasonable word count tolerance: 30% deviation from target
    WORD_COUNT_TOLERANCE = 0.30
    
    def evaluate(
        self,
        intent: WritingIntent,
        draft_before: str,
        draft_after: str
    ) -> IntentPreservationResult:
        """
        Evaluates intent preservation across a revision.
        Returns structured results with clear status per check.
        """
        results = {}
        
        # 1. Genre preservation (heuristic: check if genre keyword appears, 
        #    but genre presence in text is not always literal)
        results["genre"] = self._check_genre(intent.genre, draft_before, draft_after)
        
        # 2. POV preservation
        results["pov"] = self._check_pov(intent.pov, draft_before, draft_after)
        
        # 3. Word count compliance
        results["word_count"] = self._check_word_count(intent.length, draft_after)
        
        # 4. Required facts / constraints
        results["constraints"] = self._check_constraints(intent.constraints, draft_after)
        
        # 5. Named entity preservation
        results["named_entities"] = self._check_named_entities(draft_before, draft_after)
        
        # 6. Tone (requires LLM evaluation — explicitly marked)
        results["tone"] = {
            "status": "requires_evaluation",
            "method": "qualitative_or_llm",
            "requested_tone": intent.tone,
            "reason": "Tonal consistency cannot be reliably measured with deterministic checks."
        }
        
        # 7. Semantic plot consistency (requires LLM evaluation)
        results["semantic_plot_consistency"] = {
            "status": "requires_evaluation",
            "method": "qualitative_or_llm",
            "reason": "Plot-level semantic consistency requires qualitative comparison."
        }
        
        failed_checks = []
        if results["pov"]["status"] == "possibly_changed":
            failed_checks.append("pov")
        if results["word_count"]["status"] == "out_of_range":
            failed_checks.append("word_count")
            
        status = "fail" if failed_checks else "pass"
        
        return IntentPreservationResult(
            status=status,
            length_preserved=results["word_count"]["status"] == "within_range",
            pov_preserved=results["pov"]["status"] in ("preserved", "requires_evaluation"),
            failed_checks=failed_checks,
            details=results
        )
    
    def _check_genre(self, requested_genre: str, before: str, after: str) -> Dict[str, Any]:
        """
        Genre is a structural property, not a keyword.
        We can't reliably verify genre from text alone without LLM analysis.
        However, we can check if the NarrativeProfile's SIT_GEN_001 feature is consistent.
        """
        return {
            "status": "requires_evaluation",
            "method": "profile_feature_comparison",
            "requested_genre": requested_genre,
            "reason": "Genre consistency should be verified via SIT_GEN_001 feature comparison, not keyword search."
        }
    
    def _check_pov(self, requested_pov: str, before: str, after: str) -> Dict[str, Any]:
        """
        Heuristic POV check using pronoun frequency patterns.
        """
        pov_key = requested_pov.lower().strip()
        expected_patterns = None
        for label, patterns in self.POV_PATTERNS.items():
            if label in pov_key:
                expected_patterns = patterns
                break
        
        if expected_patterns is None:
            return {
                "status": "requires_evaluation",
                "method": "qualitative",
                "requested_pov": requested_pov,
                "reason": f"No heuristic pattern defined for POV '{requested_pov}'."
            }
        
        # Count pattern matches in both drafts
        before_lower = f" {before.lower()} "
        after_lower = f" {after.lower()} "
        
        before_hits = sum(1 for p in expected_patterns if p.lower() in before_lower)
        after_hits = sum(1 for p in expected_patterns if p.lower() in after_lower)
        
        before_present = before_hits > 0
        after_present = after_hits > 0
        
        if before_present and after_present:
            status = "preserved"
        elif not before_present and not after_present:
            status = "requires_evaluation"
        elif before_present and not after_present:
            status = "possibly_changed"
        else:
            status = "requires_evaluation"
        
        return {
            "status": status,
            "method": "pronoun_heuristic",
            "requested_pov": requested_pov,
            "before_pattern_matches": before_hits,
            "after_pattern_matches": after_hits
        }
    
    def _check_word_count(self, target_length: int, draft: str) -> Dict[str, Any]:
        """
        Checks if the revised draft is within tolerance of the requested length.
        """
        actual_count = len(draft.split())
        lower_bound = int(target_length * (1 - self.WORD_COUNT_TOLERANCE))
        upper_bound = int(target_length * (1 + self.WORD_COUNT_TOLERANCE))
        
        within_range = lower_bound <= actual_count <= upper_bound
        
        return {
            "status": "within_range" if within_range else "out_of_range",
            "method": "deterministic",
            "requested_length": target_length,
            "actual_length": actual_count,
            "tolerance": f"±{int(self.WORD_COUNT_TOLERANCE * 100)}%",
            "bounds": {"lower": lower_bound, "upper": upper_bound}
        }
    
    def _check_constraints(self, constraints: List[str], draft: str) -> Dict[str, Any]:
        """
        Checks if explicit constraints are at least referenced in the draft.
        This is a weak heuristic; semantic verification requires LLM.
        """
        if not constraints:
            return {"status": "no_constraints_specified"}
        
        results = []
        for constraint in constraints:
            # Simple keyword presence check (acknowledged as weak)
            words = constraint.lower().split()
            key_terms = [w for w in words if len(w) > 3]  # Skip short words
            if key_terms:
                found = any(term in draft.lower() for term in key_terms)
                results.append({
                    "constraint": constraint,
                    "keyword_presence": "found" if found else "not_found",
                    "method": "keyword_heuristic",
                    "note": "Keyword presence is a weak proxy. Semantic verification requires evaluation."
                })
            else:
                results.append({
                    "constraint": constraint,
                    "keyword_presence": "requires_evaluation",
                    "method": "no_key_terms_extracted"
                })
        
        return {
            "status": "checked",
            "method": "keyword_heuristic",
            "checks": results
        }
    
    def _check_named_entities(self, before: str, after: str) -> Dict[str, Any]:
        """
        Heuristic check: extracts capitalized multi-char words as potential named entities
        from Draft 0 and checks if they appear in Draft 1.
        
        This is a rough heuristic. Proper NER would require a dedicated model.
        """
        def extract_potential_names(text: str) -> set:
            words = text.split()
            names = set()
            for i, word in enumerate(words):
                # Skip first word of sentences (could be any capitalized word)
                if i > 0 and word[0:1].isupper() and len(word) > 1:
                    clean = word.strip(".,;:!?\"'()[]")
                    if clean and clean[0].isupper() and not clean.isupper():
                        names.add(clean)
            return names
        
        before_names = extract_potential_names(before)
        after_names = extract_potential_names(after)
        
        if not before_names:
            return {
                "status": "no_entities_detected",
                "method": "capitalization_heuristic"
            }
        
        preserved = before_names & after_names
        missing = before_names - after_names
        new_in_after = after_names - before_names
        
        return {
            "status": "checked",
            "method": "capitalization_heuristic",
            "entities_in_draft_0": sorted(before_names),
            "preserved_in_draft_1": sorted(preserved),
            "missing_from_draft_1": sorted(missing),
            "new_in_draft_1": sorted(new_in_after),
            "preservation_ratio": len(preserved) / len(before_names) if before_names else None,
            "note": "Capitalization-based extraction is a heuristic. Some entities may be missed or falsely detected."
        }
