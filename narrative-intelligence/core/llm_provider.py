import os
from typing import Dict, Any
from core.llm.router import ProviderRouter

class LLMProvider:
    """Wrapper for ProviderRouter to maintain compatibility."""
    
    def __init__(self, agent: str = "lens"):
        self.router = ProviderRouter(agent)
        
    @property
    def provider(self) -> str:
        return self.router.provider

    @property
    def model(self) -> str:
        return self.router.model

    @property
    def last_metadata(self) -> Dict[str, Any]:
        return self.router.last_metadata
        
    def is_configured(self) -> bool:
        return self.router.is_configured()
        
    def get_structured_output(self, prompt: str, schema: Dict[str, Any]) -> str:
        return self.router.get_structured_output(prompt, schema)
        
    def generate_text(self, prompt: str) -> str:
        return self.router.generate_text(prompt)
