import os
import json
import requests
import time
from typing import Dict, Any
from core.llm.provider import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self, model: str):
        self._model = model

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _get_api_key(self) -> str:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise Exception("GEMINI_API_KEY not configured")
        return key

    def generate_text(self, prompt: str) -> str:
        api_key = self._get_api_key()
        model_name = self._model.replace("gemini/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        for attempt in range(5):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            except requests.exceptions.RequestException as e:
                if attempt < 4:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise Exception(f"Network Error: {str(e)}")

            if response.status_code == 200:
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code in [429, 503, 500]:
                time.sleep(2 * (attempt + 1))
                continue
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
        raise Exception(f"API Error: Retries exhausted. Last status {response.status_code}")

    def get_structured_output(self, prompt: str, schema: Dict[str, Any]) -> str:
        api_key = self._get_api_key()
        model_name = self._model.replace("gemini/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        prompt_text = f"You are a narrative analyzer. Output JSON only. Format: {json.dumps(schema)}. Text to analyze: {prompt}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        for attempt in range(5):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            except requests.exceptions.RequestException as e:
                if attempt < 4:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise Exception(f"Network Error: {str(e)}")

            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                
                try:
                    content_clean = content.strip()
                    if content_clean.startswith("```json"):
                        content_clean = content_clean[7:]
                    if content_clean.endswith("```"):
                        content_clean = content_clean[:-3]
                    json.loads(content_clean)
                except json.JSONDecodeError:
                    raise Exception("Malformed JSON")
                    
                return content
            elif response.status_code in [429, 503, 500]:
                time.sleep(2 * (attempt + 1))
                continue
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
        raise Exception(f"API Error: Retries exhausted. Last status {response.status_code}")

    def health_check(self) -> bool:
        try:
            self.generate_text("Say hi")
            schema = {"type": "object", "properties": {"hi": {"type": "string"}}}
            self.get_structured_output("Say hi", schema)
            return True
        except Exception:
            return False
