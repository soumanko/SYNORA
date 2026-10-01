import os
import sys
import json
import yaml
import uuid
import argparse
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.llm_provider import LLMProvider
from core.taxonomy.taxonomy_loader import TaxonomyLoader
from core.analysis.core30 import Core30Selector
from core.extraction.dimension_analyzer import FeatureExtractor
from agents.lens.analyzer import NarrativeLensAnalyzer
from core.diagnostics.diagnostic_engine import DiagnosticEngine
from agents.forge.revision_planner import RevisionPlanner
from agents.forge.revision_agent import RevisionAgent
from core.evaluation.revision_effect import RevisionEffectEvaluator
from core.evaluation.intent_preservation import IntentPreservationEvaluator
from core.evaluation.quality_gate import QualityGate
from agents.forge.orchestrator import ForgeOrchestrator
from agents.forge.generator import NarrativeForgeGenerator, WritingIntent
from evaluation.schemas.run_schema import EvaluationRun, DraftRecord, RevisionHistoryRecord

def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_prompts(path: str, limit: int = None) -> List[Dict[str, Any]]:
    prompts = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
    if limit:
        return prompts[:limit]
    return prompts

def run_baseline(prompt: Dict[str, Any], generator: NarrativeForgeGenerator, analyzer: NarrativeLensAnalyzer, run_id: str) -> EvaluationRun:
    intent = WritingIntent(
        prompt=prompt["prompt"],
        genre=prompt["genre"],
        tone=prompt["tone"],
        pov=prompt["pov"],
        length=prompt["target_length"],
        constraints=prompt["required_facts"]
    )
    
    start_time = datetime.utcnow().isoformat() + "Z"
    
    draft_0 = generator.generate_initial_draft(intent)
    prof = analyzer.analyze_document(draft_0["content"], "draft_0")
    
    draft_record = DraftRecord(
        version="draft_0",
        content=draft_0["content"],
        word_count=len(draft_0["content"].split()),
        profile=prof.dict(),
        diagnostics=None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="baseline",
        provider="gemini",
        model="gemini-3.5-flash-lite",
        generation_config={"temperature": 0.7, "max_output_tokens": 1024},
        analysis_mode="core",
        core30_source="core30_approximation.json",
        status="success",
        drafts=[draft_record],
        revision_history=[],
        metrics={},
        errors=[],
        started_at=start_time,
        completed_at=datetime.utcnow().isoformat() + "Z"
    )

def run_prompt_revision(prompt: Dict[str, Any], generator: NarrativeForgeGenerator, analyzer: NarrativeLensAnalyzer, run_id: str, llm: LLMProvider) -> EvaluationRun:
    intent = WritingIntent(
        prompt=prompt["prompt"],
        genre=prompt["genre"],
        tone=prompt["tone"],
        pov=prompt["pov"],
        length=prompt["target_length"],
        constraints=prompt["required_facts"]
    )
    
    start_time = datetime.utcnow().isoformat() + "Z"
    
    draft_0 = generator.generate_initial_draft(intent)
    prof_0 = analyzer.analyze_document(draft_0["content"], "draft_0")
    
    draft_record_0 = DraftRecord(
        version="draft_0",
        content=draft_0["content"],
        word_count=len(draft_0["content"].split()),
        profile=prof_0.dict(),
        diagnostics=None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    rev_prompt = (
        f"Here is a draft:\n\n{draft_0['content']}\n\n"
        f"Revise the draft to improve its narrative quality while preserving the "
        f"original intent, meaning, genre, tone, point of view, required facts, "
        f"and approximate length. Return ONLY the revised text."
    )
    
    schema = {
        "type": "object",
        "properties": {
            "revised_content": {"type": "string"}
        },
        "required": ["revised_content"]
    }
    
    res = llm.get_structured_output(rev_prompt, schema)
    try:
        content_1 = json.loads(res).get("revised_content", "")
    except Exception:
        content_1 = res # fallback
        
    prof_1 = analyzer.analyze_document(content_1, "draft_1")
    
    draft_record_1 = DraftRecord(
        version="draft_1",
        content=content_1,
        word_count=len(content_1.split()),
        profile=prof_1.dict(),
        diagnostics=None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="prompt_revision",
        provider="gemini",
        model="gemini-3.5-flash-lite",
        generation_config={"temperature": 0.7, "max_output_tokens": 1024},
        analysis_mode="core",
        core30_source="core30_approximation.json",
        status="success",
        drafts=[draft_record_0, draft_record_1],
        revision_history=[],
        metrics={},
        errors=[],
        started_at=start_time,
        completed_at=datetime.utcnow().isoformat() + "Z"
    )

def run_narrative_forge(prompt: Dict[str, Any], orchestrator: ForgeOrchestrator, run_id: str, max_cycles: int = 3) -> EvaluationRun:
    intent = WritingIntent(
        prompt=prompt["prompt"],
        genre=prompt["genre"],
        tone=prompt["tone"],
        pov=prompt["pov"],
        length=prompt["target_length"],
        constraints=prompt["required_facts"]
    )
    
    start_time = datetime.utcnow().isoformat() + "Z"
    
    state = orchestrator.execute_run(intent, max_cycles=max_cycles, run_id=run_id)
    
    drafts = []
    for v in state.versions:
        drafts.append(DraftRecord(
            version=v.version,
            content=v.content,
            word_count=len(v.content.split()),
            profile=v.narrative_profile,
            diagnostics=v.diagnostics,
            timestamp=datetime.utcnow().isoformat() + "Z"
        ))
        
    rev_hist = []
    for r in state.revisions:
        rev_hist.append(RevisionHistoryRecord(
            cycle=r.revision_number,
            revision_plan=r.plan,
            revision_effect=r.effect,
            intent_preservation=r.intent_preservation,
            quality_gate=r.quality_report,
            timestamp=datetime.utcnow().isoformat() + "Z"
        ))
        
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="narrative_forge",
        provider="gemini",
        model="gemini-3.5-flash-lite",
        generation_config={"temperature": 0.7, "max_output_tokens": 1024},
        analysis_mode="core",
        core30_source="core30_approximation.json",
        status=state.status,
        drafts=drafts,
        revision_history=rev_hist,
        metrics={},
        errors=[state.stop_reason] if state.stop_reason else [],
        started_at=start_time,
        completed_at=datetime.utcnow().isoformat() + "Z"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="evaluation/config/phase14.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    config = load_config(args.config)
    prompts = load_prompts(config["dataset"]["path"], args.limit)
    
    if "prompt_ids" in config.get("dataset", {}):
        prompts = [p for p in prompts if p["prompt_id"] in config["dataset"]["prompt_ids"]]
        
    if "pilot" in args.config and len(prompts) > 4:
        raise ValueError("Pilot configuration must not run more than 4 prompts to prevent full experiment launch.")
    
    if args.dry_run:
        print(f"DRY RUN: Loaded {len(prompts)} prompts. Configuration verified.")
        max_cycles = config.get("forge", {}).get("max_cycles", 3)
        calls_per_prompt = 0
        if "baseline" in config["systems"]:
            calls_per_prompt += 2
        if "prompt_revision" in config["systems"]:
            calls_per_prompt += 4
        if "narrative_forge" in config["systems"]:
            calls_per_prompt += 2 + (max_cycles * 2)
            
        total_calls = calls_per_prompt * len(prompts)
        print(f"Estimated maximum LLM calls: {total_calls}")
        return
        
    # Initialization
    tax_loader = TaxonomyLoader("data/storyscope/taxonomy.json", "data/storyscope/core30_approximation.json")
    taxonomy = tax_loader.load_taxonomy()
    core30 = tax_loader.load_core30()
    core30_selector = Core30Selector(core30)
    
    llm = LLMProvider()
    extractor = FeatureExtractor(taxonomy, llm)
    
    lens = NarrativeLensAnalyzer(extractor, None, core30_selector, taxonomy)
    forge = NarrativeForgeGenerator(llm)
    
    diag_engine = DiagnosticEngine(taxonomy)
    planner = RevisionPlanner(diag_engine, taxonomy)
    agent = RevisionAgent(llm)
    effect_eval = RevisionEffectEvaluator(taxonomy)
    intent_eval = IntentPreservationEvaluator()
    qg = QualityGate()
    
    orchestrator = ForgeOrchestrator(forge, lens, core30_selector, diag_engine, planner, agent, effect_eval, intent_eval, qg, taxonomy)
    
    output_dir = os.path.join(config["output"]["directory"], datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(output_dir, exist_ok=True)
    
    run_file = os.path.join(output_dir, "runs.jsonl")
    
    for prompt in prompts:
        for system in config["systems"]:
            run_id = str(uuid.uuid4())
            print(f"Running {system} for {prompt['prompt_id']} (Run ID: {run_id})")
            try:
                if system == "baseline":
                    run = run_baseline(prompt, forge, lens, run_id)
                elif system == "prompt_revision":
                    run = run_prompt_revision(prompt, forge, lens, run_id, llm)
                elif system == "narrative_forge":
                    max_cycles = config.get("forge", {}).get("max_cycles", 3)
                    run = run_narrative_forge(prompt, orchestrator, run_id, max_cycles=max_cycles)
                else:
                    continue
                    
                with open(run_file, "a") as f:
                    f.write(run.model_dump_json() + "\n")
            except Exception as e:
                print(f"FAILED {system} on {prompt['prompt_id']}: {str(e)}")
                # Log failure
                failed_run = EvaluationRun(
                    run_id=run_id, experiment_id="phase14", prompt_id=prompt["prompt_id"], system=system, provider="gemini", model="gemini-3.5-flash-lite", generation_config={}, analysis_mode="core", core30_source="", status="failed", drafts=[], revision_history=[], metrics={}, errors=[str(e)], started_at="", completed_at=""
                )
                with open(run_file, "a") as f:
                    f.write(failed_run.model_dump_json() + "\n")

if __name__ == "__main__":
    main()
