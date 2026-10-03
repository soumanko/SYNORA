import json
from typing import Dict, Any, List
from agents.forge.generator import WritingIntent

class RevisionAgent:
    """
    Executes a structured revision plan on a draft to produce a new draft.
    Does not perform analysis itself.
    """
    
    def __init__(self, llm_provider: Any):
        self.llm_provider = llm_provider
        
    def revise_draft(self, intent: WritingIntent, current_draft: str, profile: Any, diagnostics: List[Any], revision_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revises the draft according to the supplied narrative targets while preserving intent.
        """
        if revision_plan.get("status") == "no_revision_needed" or not revision_plan.get("interventions"):
            return {
                "draft": current_draft,
                "word_count": len(current_draft.split()),
                "revision_summary": "No revision needed.",
                "applied_targets": []
            }
            
        interventions = revision_plan["interventions"]
        targets = []
        instructions = []
        for inv in interventions:
            targets.append(inv["target"]["feature_id"])
            instructions.append(f"- Target: {inv['target']['feature_name']}\n  Reason: {inv['diagnostic_reason']}\n  Instruction: {inv['revision_instruction']}")
            
        constraints = [
            f"Genre: {intent.genre}",
            f"Tone: {intent.tone}",
            f"POV: {intent.pov}",
            f"Target length: ~{intent.length} words",
            f"Original Prompt: {intent.prompt}",
            "Preserve all plot facts, named entities, and required information."
        ]
        if intent.constraints:
            constraints.extend(intent.constraints)
            
        schema = {
            "type": "object",
            "properties": {
                "draft": {"type": "string", "description": "The revised narrative text."},
                "word_count": {"type": "integer"},
                "revision_summary": {"type": "string", "description": "Short summary of what was structurally changed."}
            },
            "required": ["draft", "word_count", "revision_summary"]
        }
        
        prompt = (
            "Revise the draft according to the supplied narrative targets while preserving the author's requested intent, facts, genre, tone, POV, and plot.\n"
            "Do not insert grammar mistakes, arbitrary substitutions, or attempt to evade AI detection.\n\n"
            "A. USER INTENT AND PRESERVATION CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in constraints) + "\n\n"
            "B. REVISION TARGETS:\n" + "\n".join(instructions) + "\n\n"
            "C. CURRENT DRAFT:\n" + current_draft
        )
        
        result_json_str = self.llm_provider.get_structured_output(prompt, schema)
        
        # Cleanup potentially raw json format
        result_json_str = result_json_str.strip()
        if result_json_str.startswith("```json"):
            result_json_str = result_json_str[7:]
        if result_json_str.endswith("```"):
            result_json_str = result_json_str[:-3]
            
        try:
            result = json.loads(result_json_str)
        except json.JSONDecodeError:
            raise Exception("Failed to parse RevisionAgent structured output")
            
        return {
            "draft": result.get("draft", ""),
            "word_count": result.get("word_count", 0),
            "revision_summary": result.get("revision_summary", ""),
            "applied_targets": targets,
            "metadata": getattr(self.llm_provider, "last_metadata", {})
        }
