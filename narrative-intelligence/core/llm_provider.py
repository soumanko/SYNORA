import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List
from core.taxonomy.schemas import Feature

load_dotenv()

class LLMProvider:
    """Wrapper for LiteLLM to provide structured output extraction."""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini")
        self.model = os.getenv("LLM_MODEL", "gemini/gemini-1.5-pro")
        
    def is_configured(self) -> bool:
        if self.provider == "gemini":
            return bool(os.getenv("GEMINI_API_KEY"))
        elif self.provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        return False
        
    def get_structured_output(self, prompt: str, schema: Dict[str, Any]) -> str:
        """
        Calls the LLM to get structured JSON output matching the provided schema.
        """
        if not self.is_configured():
            raise Exception("LLM_PROVIDER_NOT_CONFIGURED")
            
        try:
            if self.provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                # Strip the "gemini/" prefix if present
                model_name = self.model.replace("gemini/", "")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                
                # We prompt the model to return JSON matching the schema
                prompt_text = f"You are a narrative analyzer. Output JSON only. Format: {json.dumps(schema)}. Text to analyze: {prompt}"
                
                payload = {
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                
                import time
                for attempt in range(5):
                    print(f"DEBUG: sending request to {model_name} (attempt {attempt+1})...")
                    response = requests.post(url, headers=headers, json=payload)
                    print(f"DEBUG: received response {response.status_code}")
                    if response.status_code == 200:
                        break
                    elif response.status_code in [429, 503, 500]:
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"API Error: {response.text}")
                else:
                    raise Exception(f"API Error: Retries exhausted. Last status {response.status_code}: {response.text}")
                    
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                return content
            else:
                raise Exception("Provider not supported directly in this environment")
                
        except Exception as e:
            raise Exception(f"LLM_EXTRACTION_FAILED: {str(e)}")
