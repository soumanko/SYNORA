import os
import json
from typing import Dict, Any, Optional
from core.llm.provider import BaseProvider
from core.llm.gemini_provider import GeminiProvider
from core.llm.groq_provider import GroqProvider

class ProviderRouter:
    def __init__(self, agent: str):
        self.agent = agent
        
        self.primary_provider_name = os.getenv(f"{agent.upper()}_PRIMARY_PROVIDER")
        self.primary_model = os.getenv(f"{agent.upper()}_PRIMARY_MODEL")
        
        self.fallback_provider_name = os.getenv(f"{agent.upper()}_FALLBACK_PROVIDER")
        self.fallback_model = os.getenv(f"{agent.upper()}_FALLBACK_MODEL")
        
        if not self.primary_provider_name or not self.primary_model:
            # Fallback to general LLM vars for backwards compat during testing
            self.primary_provider_name = os.getenv("LLM_PROVIDER", "gemini")
            self.primary_model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-pro")
            
        self.last_metadata = {}
        
        self._current_active_provider = self._create_provider(self.primary_provider_name, self.primary_model)
        
    def _create_provider(self, name: str, model: str) -> BaseProvider:
        if name == "gemini":
            return GeminiProvider(model)
        elif name == "groq":
            return GroqProvider(model)
        else:
            raise ValueError(f"Unknown provider: {name}")

    @property
    def provider(self) -> str:
        return self._current_active_provider.provider_name

    @property
    def model(self) -> str:
        return self._current_active_provider.model_name
        
    def is_configured(self) -> bool:
        return bool(self.primary_provider_name and self.primary_model)

    def _execute_with_fallback(self, func_name: str, *args, **kwargs) -> str:
        primary = self._create_provider(self.primary_provider_name, self.primary_model)
        fallback = None
        if self.fallback_provider_name and self.fallback_model:
            fallback = self._create_provider(self.fallback_provider_name, self.fallback_model)
            
        try:
            self._current_active_provider = primary
            func = getattr(primary, func_name)
            result = func(*args, **kwargs)
            
            self.last_metadata = {
                "agent": self.agent,
                "provider": primary.provider_name,
                "model": primary.model_name,
                "role": "primary",
                "attempt": 1,
                "fallback_used": False
            }
            return result
        except Exception as e:
            if fallback is None:
                raise e
            
            try:
                self._current_active_provider = fallback
                func = getattr(fallback, func_name)
                result = func(*args, **kwargs)
                
                self.last_metadata = {
                    "agent": self.agent,
                    "provider": fallback.provider_name,
                    "model": fallback.model_name,
                    "role": "fallback",
                    "attempt": 2,
                    "fallback_used": True
                }
                return result
            except Exception as fallback_e:
                raise Exception(f"Primary ({primary.provider_name}) failed: {str(e)}. Fallback ({fallback.provider_name}) failed: {str(fallback_e)}")
                
    def generate_text(self, prompt: str) -> str:
        return self._execute_with_fallback("generate_text", prompt)

    def get_structured_output(self, prompt: str, schema: Dict[str, Any]) -> str:
        return self._execute_with_fallback("get_structured_output", prompt, schema)

    def health_check(self) -> bool:
        try:
            primary = self._create_provider(self.primary_provider_name, self.primary_model)
            if not primary.health_check():
                return False
            
            if self.fallback_provider_name and self.fallback_model:
                fallback = self._create_provider(self.fallback_provider_name, self.fallback_model)
                if not fallback.health_check():
                    return False
            return True
        except:
            return False

def health_check_provider(provider_name: str, model_name: str) -> bool:
    if provider_name == "gemini":
        return GeminiProvider(model_name).health_check()
    elif provider_name == "groq":
        return GroqProvider(model_name).health_check()
    return False

def health_check_agent(agent: str) -> bool:
    router = ProviderRouter(agent)
    return router.health_check()
