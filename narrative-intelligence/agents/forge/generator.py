import json
import uuid
from typing import Dict, Any, List

class WritingIntent:
    def __init__(self, prompt: str, genre: str, tone: str, pov: str, length: int, constraints: List[str] = None):
        self.prompt = prompt
        self.genre = genre
        self.tone = tone
        self.pov = pov
        self.length = length
        self.constraints = constraints or []

class NarrativeForgeGenerator:
    """
    Core generator for the Narrative Forge agent.
    Handles the initial generation based on writing intent.
    """
    
    def __init__(self, llm_provider: Any):
        self.llm_provider = llm_provider
        
    def generate_initial_draft(self, intent: WritingIntent) -> Dict[str, Any]:
        """
        Generates the initial draft based on the parsed user intent.
        Returns a Draft 0 object with content and metadata.
        """
        schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The generated narrative draft text."},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "word_count": {"type": "integer"}
                    },
                    "required": ["word_count"]
                }
            },
            "required": ["content", "metadata"]
        }
        
        prompt = (
            f"Generate a narrative with the following constraints:\n"
            f"Prompt: {intent.prompt}\n"
            f"Genre: {intent.genre}\n"
            f"Tone: {intent.tone}\n"
            f"POV: {intent.pov}\n"
            f"Target Length: {intent.length} words\n"
        )
        if intent.constraints:
            prompt += f"Constraints: {', '.join(intent.constraints)}\n"
            
        result_json_str = self.llm_provider.get_structured_output(prompt, schema)
        
        # Strip potential markdown formatting from LLM response
        result_json_str = result_json_str.strip()
        if result_json_str.startswith("```json"):
            result_json_str = result_json_str[7:]
        if result_json_str.endswith("```"):
            result_json_str = result_json_str[:-3]
            
        result = json.loads(result_json_str)
        
        return {
            "draft_id": "draft_0",
            "content": result.get("content", ""),
            "metadata": {
                "model": getattr(self.llm_provider, "model", "unknown"),
                "provider": getattr(self.llm_provider, "provider", "unknown"),
                **getattr(self.llm_provider, "last_metadata", {}),
                "word_count": result.get("metadata", {}).get("word_count", 0)
            }
        }
        
    def revise_draft(self, current_draft: str, intent: WritingIntent, revision_plan: Dict[str, Any]) -> str:
        """
        Revises the draft based on diagnostic recommendations while preserving intent.
        """
        # Placeholder for phase 8
        return "Revised text..."
