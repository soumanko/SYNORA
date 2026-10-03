from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass

    @abstractmethod
    def get_structured_output(self, prompt: str, schema: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass
