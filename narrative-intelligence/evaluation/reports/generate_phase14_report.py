import os
import sys
import json
import argparse
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from evaluation.schemas.run_schema import EvaluationRun
from evaluation.metrics.targeted_movement import calculate_targeted_movement
from evaluation.metrics.incidental_movement import calculate_incidental_movement
from evaluation.metrics.intent import calculate_intent_preservation
from evaluation.metrics.feature_distance import calculate_profile_distance
from evaluation.metrics.performance import calculate_performance

def load_runs(path: str) -> List[EvaluationRun]:
    runs = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    runs.append(EvaluationRun.model_validate_json(line))
                except Exception as e:
                    print(f"Skipping malformed run: {e}")
    return runs

def generate_report(runs: List[EvaluationRun], output_path: str):
    # This is a stub for the full report generation logic.
    # A full implementation would aggregate metrics across all runs and generate a markdown file.
    with open(output_path, "w") as f:
        f.write("# Phase 14 Evaluation Report\n\n")
        f.write("## 1. Research Question\nDoes narrative-feedback-driven revision produce measurable changes...\n\n")
        f.write("## 2. Experimental Setup\nProvider: Gemini, Model: 3.5 Flash Lite\n\n")
        
        baseline_runs = [r for r in runs if r.system == "baseline"]
        forge_runs = [r for r in runs if r.system == "narrative_forge"]
        
        f.write(f"Total Runs: {len(runs)}\n")
        f.write(f"Baseline Runs: {len(baseline_runs)}\n")
        f.write(f"Forge Runs: {len(forge_runs)}\n\n")
        
        f.write("## 12. Failure Analysis\n")
        failed = [r for r in runs if r.status != "success"]
        for r in failed:
            f.write(f"- {r.run_id}: {r.errors}\n")
            
        f.write("\n## 13. Limitations\n")
        f.write("- Core30 approximation rather than official SHAP Core30\n")
        f.write("- Core mode rather than full 304 mode\n")
        f.write("- provider quota limitations\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    runs = load_runs(args.runs)
    generate_report(runs, args.output)
    print(f"Report generated at {args.output}")
