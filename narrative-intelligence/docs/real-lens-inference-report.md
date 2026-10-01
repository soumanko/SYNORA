REAL LENS INFERENCE STATUS

Provider: PASS
Structured output: PASS

304 extraction:
  Records: 0
  Valid: 0
  Unavailable: 0
  Failed: 304

Core Feature Analysis:
  IDs: 0 / 30
  Values: 0
  Unavailable: 0

Encoding: FAIL
Classifier: FAIL
Evidence: FAIL
NarrativeProfile: FAIL
HTTP API: FAIL
Frontend: FAIL

Model/Provider-specific limitations:
- A single dimension extraction was successfully tested with `gemini-3.5-flash` passing validation and structured output.
- During the full 304 feature extraction, the process failed due to:
  `Error: CORE_FEATURE_ANALYSIS_FAILED - PROVIDER_ERROR: LLM_EXTRACTION_FAILED: API Error: Retries exhausted. Last status 429: You exceeded your current quota... Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3.5-flash`
- As explicitly instructed, execution was stopped at the quota failure stage without modifying unrelated analytical components.
