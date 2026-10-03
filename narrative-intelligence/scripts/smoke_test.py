import os
import time
import json
from dotenv import load_dotenv
from core.llm.gemini_provider import GeminiProvider
from core.llm.groq_provider import GroqProvider
from core.llm.router import ProviderRouter

def run_tests():
    load_dotenv()
    
    results = []
    
    # TEST 1: GEMINI
    try:
        t0 = time.time()
        gemini = GeminiProvider("gemini-3.5-flash-lite")
        text_resp = gemini.generate_text("Say hi")
        schema = {"type": "object", "properties": {"hi": {"type": "string"}}}
        json_resp = gemini.get_structured_output("Say hi", schema)
        latency = time.time() - t0
        results.append(f"**TEST 1: GEMINI**\n- Status: SUCCESS\n- Model: {gemini.model_name}\n- Text Output: {text_resp}\n- JSON Output: {json_resp}\n- Latency: {latency:.2f}s\n")
    except Exception as e:
        results.append(f"**TEST 1: GEMINI**\n- Status: FAILED\n- Error: {str(e)}\n")

    # TEST 2: GROQ GPT-OSS
    try:
        t0 = time.time()
        groq = GroqProvider("openai/gpt-oss-120b")
        text_resp = groq.generate_text("Say hi")
        schema = {"type": "object", "properties": {"hi": {"type": "string"}}}
        json_resp = groq.get_structured_output("Say hi", schema)
        latency = time.time() - t0
        results.append(f"**TEST 2: GROQ GPT-OSS**\n- Status: SUCCESS\n- Model: {groq.model_name}\n- Text Output: {text_resp}\n- JSON Output: {json_resp}\n- Latency: {latency:.2f}s\n")
    except Exception as e:
        results.append(f"**TEST 2: GROQ GPT-OSS**\n- Status: FAILED\n- Error: {str(e)}\n")

    # TEST 3 & 4: AGENT ROUTING & METADATA
    try:
        # Forcing environment for Lens and Forge
        os.environ["LENS_PRIMARY_PROVIDER"] = "gemini"
        os.environ["LENS_PRIMARY_MODEL"] = "gemini-3.5-flash-lite"
        os.environ["LENS_FALLBACK_PROVIDER"] = "groq"
        os.environ["LENS_FALLBACK_MODEL"] = "openai/gpt-oss-120b"
        
        os.environ["FORGE_PRIMARY_PROVIDER"] = "groq"
        os.environ["FORGE_PRIMARY_MODEL"] = "openai/gpt-oss-120b"
        os.environ["FORGE_FALLBACK_PROVIDER"] = "gemini"
        os.environ["FORGE_FALLBACK_MODEL"] = "gemini-3.5-flash-lite"
        
        lens_router = ProviderRouter("lens")
        try:
            lens_router.generate_text("Say hi")
            lens_meta = json.dumps(lens_router.last_metadata)
            results.append(f"**TEST 3 & 4: LENS ROUTING & METADATA**\n- Status: SUCCESS\n- Metadata: {lens_meta}\n")
        except Exception as e:
            results.append(f"**TEST 3 & 4: LENS ROUTING & METADATA**\n- Status: FAILED\n- Error: {str(e)}\n")

        forge_router = ProviderRouter("forge")
        try:
            forge_router.generate_text("Say hi")
            forge_meta = json.dumps(forge_router.last_metadata)
            results.append(f"**TEST 3 & 4: FORGE ROUTING & METADATA**\n- Status: SUCCESS\n- Metadata: {forge_meta}\n")
        except Exception as e:
            results.append(f"**TEST 3 & 4: FORGE ROUTING & METADATA**\n- Status: FAILED\n- Error: {str(e)}\n")
            
    except Exception as e:
        results.append(f"**TEST 3 & 4: ROUTING & METADATA setup**\n- Status: FAILED\n- Error: {str(e)}\n")

    with open("evaluation/reports/dual_brain_smoke_test.md", "w", encoding="utf-8") as f:
        f.write("# Dual-Brain Real Provider Smoke Test\n\n")
        f.write("\n".join(results))
        if "FAILED" in "".join(results):
            f.write("\n\n**NOT READY FOR PHASE 14**\n")
        else:
            f.write("\n\n**READY FOR PHASE 14**\n")

if __name__ == "__main__":
    run_tests()
