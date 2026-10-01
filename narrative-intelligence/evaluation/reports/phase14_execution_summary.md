# Phase 14 Execution Summary

## Overview
- **Experiment ID**: 2026-10-01
- **Prompts Attempted**: 13
- **Successful Runs**: 0
- **Failed Runs**: 33
- **Partial Runs**: 6

## Results by System
- **Baseline**: 13 attempted (all failed/partial)
- **Prompt Revision**: 13 attempted (all failed/partial)
- **Narrative Forge**: 13 attempted (all failed/partial)

## Error Analysis
- **Provider Failures / Quota Failures**: Yes (HTTP 429 encountered extensively limiting success)
- **Timeout Failures**: 0

## Coverage and Runtime
- **Total LLM Calls**: 0 successful (calls were made but retries exhausted due to 429)
- **Total Runtime**: N/A (aborted early due to quota exhaustion)
- **Analysis Coverage**: Low/None
- **Metric Coverage**: Low/None

## Data Integrity Note
- Every attempted run has a persisted record.
- No failed run was replaced by fabricated data.
- Core30 source remains exactly as identified (XGBoost approximation).
- Unavailable metrics remained explicitly unavailable.
