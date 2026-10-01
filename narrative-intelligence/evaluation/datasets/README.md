# Phase 14 Evaluation Dataset

## Purpose
This dataset is designed to evaluate the narrative-feedback-driven revision capabilities of the Narrative Forge, comparing it against simpler baselines (normal generation and prompt-only revision).

## Contents
- **Total Prompts:** 12
- **Genres:** Mystery (3), Sci-Fi (3), Literary/Drama (3), Thriller (3)
- **Dataset Version:** 1.0

## Schema
Each prompt follows this schema:
```json
{
  "prompt_id": "...",
  "genre": "...",
  "tone": "...",
  "pov": "...",
  "target_length": 0,
  "prompt": "...",
  "required_facts": ["..."],
  "seed": 0
}
```

## Generation Assumptions
- The LLM will strictly adhere to the deterministic intent checks (POV, required facts, target word count within 30% tolerance).
- Tone and semantic plot consistencies require qualitative assessment and are not fully deterministically checked.
