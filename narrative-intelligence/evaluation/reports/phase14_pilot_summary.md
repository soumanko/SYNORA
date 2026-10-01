# Phase 14A Pilot Summary

## Overview
- **Total Runs Attempted**: 12
- **Successful Runs**: 0
- **Partial Runs**: 0
- **Failed Runs**: 12

## Results by System
- **Baseline**: 4 attempted (4 failed)
- **Prompt Revision**: 4 attempted (4 failed)
- **Narrative Forge**: 4 attempted (4 failed)

## Results by Genre
- **Mystery (MYS_001)**: 3 runs
- **Sci-Fi (SCI_001)**: 3 runs
- **Literary/Drama (LIT_001)**: 3 runs
- **Thriller (THR_001)**: 3 runs

## Error and Provider Metrics
- **Provider Errors**: 12 (HTTP 429 Quota Exceeded on all attempts)
- **Total LLM Calls**: 0 (calls made, retries exhausted due to rate limits)
- **Latency**: N/A (aborted due to API errors)

## Coverage Metrics
- **Analysis Coverage**: 0%
- **Targeted Movement Coverage**: 0%
- **Intent-Preservation Coverage**: 0%

## Integrity Check
- All attempted runs are persisted.
- No successful output was duplicated into another system.
- Baseline contains no revision.
- Prompt Revision contains only the generic revision.
- Forge contains the StoryScope-feedback revision loop.
- Core30 is correctly identified as the XGBoost approximation.
- Unavailable metrics remain explicitly unavailable.
- No fabricated values exist.
