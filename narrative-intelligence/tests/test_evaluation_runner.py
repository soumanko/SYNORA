import pytest
import json
import os
from evaluation.experiments.phase14_baseline_vs_forge import load_prompts, load_config
from evaluation.schemas.run_schema import EvaluationRun

def test_load_prompts():
    # Make a dummy dataset
    os.makedirs("evaluation/datasets", exist_ok=True)
    with open("evaluation/datasets/dummy.jsonl", "w") as f:
        f.write(json.dumps({"prompt_id": "test", "prompt": "a", "genre": "a", "tone": "a", "pov": "a", "target_length": 1, "required_facts": []}) + "\n")
        
    prompts = load_prompts("evaluation/datasets/dummy.jsonl")
    assert len(prompts) == 1
    assert prompts[0]["prompt_id"] == "test"
    
def test_evaluation_run_schema():
    # Should not throw validation error
    run = EvaluationRun(
        run_id="r1",
        experiment_id="e1",
        prompt_id="p1",
        system="baseline",
        provider="gemini",
        model="gemini-3.5-flash-lite",
        generation_config={},
        analysis_mode="core",
        core30_source="core30_approximation.json",
        status="success",
        drafts=[],
        revision_history=[],
        metrics={},
        errors=[],
        started_at="2026-10-01T00:00:00Z",
        completed_at="2026-10-01T00:00:00Z"
    )
    assert run.run_id == "r1"
