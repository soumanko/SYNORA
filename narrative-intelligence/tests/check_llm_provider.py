import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.llm_provider import LLMProvider

def check_provider():
    provider = LLMProvider()
    print(f"Provider: {provider.provider if provider.provider else 'missing'}")
    print(f"Model: {provider.model if provider.model else 'missing'}")
    
    is_configured = provider.is_configured()
    print(f"API key: {'present' if is_configured else 'missing'}")
    
    # Check connectivity and structured output
    print("Connectivity: ", end="")
    if not is_configured:
        print("FAIL (No API Key)")
        print("Structured output: FAIL")
        return
        
    try:
        # Simple extraction test to verify structured output works
        schema = {"test_feature": {"value": "string", "confidence": "float"}}
        res = provider.get_structured_output("Test the connectivity", schema)
        print("PASS")
        print("Structured output: PASS")
    except Exception as e:
        print(f"FAIL ({str(e)})")
        print("Structured output: FAIL")

if __name__ == "__main__":
    check_provider()
