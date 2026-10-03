# Dual-Brain Real Provider Smoke Test

**TEST 1: GEMINI**
- Status: SUCCESS
- Model: gemini-3.5-flash-lite
- Text Output: Hi! How can I help you today?
- JSON Output: {
  "hi": "Say hi"
}
- Latency: 2.69s

**TEST 2: GROQ GPT-OSS**
- Status: SUCCESS
- Model: openai/gpt-oss-120b
- Text Output: Hello! 👋 How can I assist you today?
- JSON Output: {"hi":"hi"}
- Latency: 2.33s

**TEST 3 & 4: LENS ROUTING & METADATA**
- Status: SUCCESS
- Metadata: {"agent": "lens", "provider": "gemini", "model": "gemini-3.5-flash-lite", "role": "primary", "attempt": 1, "fallback_used": false}

**TEST 3 & 4: FORGE ROUTING & METADATA**
- Status: SUCCESS
- Metadata: {"agent": "forge", "provider": "groq", "model": "openai/gpt-oss-120b", "role": "primary", "attempt": 1, "fallback_used": false}


**READY FOR PHASE 14**
