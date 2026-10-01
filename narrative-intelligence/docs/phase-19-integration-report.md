# Phase 19: Integration Report

## StoryScope Integration
* **Commit/Version**: Main branch (`storyscope-main` archive)
* **Taxonomy Validation**: 
  - PASSED
  - 304 valid features across 10 dimensions. No duplicates or invalid types.
* **Model Validation**: 
  - PASSED
  - Loaded `binary_full.json` (462 features, binary), `binary_narrative.json` (410 features, binary)
  - Loaded `multiclass_full.json` (462 features, 6 classes), `multiclass_narrative.json` (410 features, 6 classes)
* **Encoder Validation**: 
  - PASSED
  - Verified exact feature names expected by XGBoost models.
* **Core30 Derivation**: 
  - LIMITATION DOCUMENTED
  - The official SHAP implementation (`storyscope/6_classification/shap_analysis.py`) genuinely cannot be reproduced. Execution fails with `ImportError: DLL load failed while importing _sparsetools: An Application Control policy has blocked this file`. This OS-level Application Control policy blocks `scipy.sparse` (a dependency of `shap`), rendering the official SHAP algorithm unrunnable on this host.
  - As a result, no claim of official Core30 reproduction is made. The system instead uses an explicitly labeled approximation (`data/storyscope/core30_approximation.json`) based on XGBoost split-frequency importance.

## Pipeline Integration
* **304 Extraction**: PASSED via schema validation tests.
* **Normalization & Encoding**: PASSED via mapping of the 304 taxonomy to the 462 encoded columns expected by the models.
* **Classification**: PASSED. The XGBoost models successfully output probabilities for the expected classes.

## Evidence Integrity
* **Offset Validation**: PASSED. String index tracking verified against source document chunks.

## Forge & Lens
* **End-to-End Tests**: PASSED structural integration.
* **Cross-Agent Consistency**: PASSED. Both agents use the exact same `NarrativeProfile` schema and `ClassifierResult`.

## Known Limitations
* **Core30 Extraction**: Cannot run TreeExplainer due to OS Application Control policy blocking scipy/shap. Using an explicitly labeled XGBoost split-frequency approximation instead.
* **Stochastic Behavior**: LLM extraction is inherently variable; retry logic is required in production to ensure all 304 features are populated without `n/a` fallbacks.
* **Domain Limitations**: Classifier is validated on Fiction only.

## Test Summary
```text
PASSED: 12
FAILED: 0
SKIPPED: 1 (Core30 exact derivation pending SHAP script)
```
