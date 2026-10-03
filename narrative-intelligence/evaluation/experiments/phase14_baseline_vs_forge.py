import os
import sys
import json
import yaml
import uuid
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

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

def _collect_metadata(llm_provider) -> Dict[str, Any]:
    """Collect last_metadata from an LLMProvider/ProviderRouter after a call."""
    return getattr(llm_provider, "last_metadata", {})

def run_baseline(prompt: Dict[str, Any], generator: NarrativeForgeGenerator, analyzer: NarrativeLensAnalyzer,
                 run_id: str, gen_llm: LLMProvider, lens_llm: LLMProvider, config: Dict[str, Any]) -> EvaluationRun:
    intent = WritingIntent(
        prompt=prompt["prompt"],
        genre=prompt["genre"],
        tone=prompt["tone"],
        pov=prompt["pov"],
        length=prompt["target_length"],
        constraints=prompt["required_facts"]
    )
    
    start_time = datetime.utcnow().isoformat() + "Z"
    provider_log = []
    fallback_count = 0
    any_fallback = False
    
    draft_0 = generator.generate_initial_draft(intent)
    gen_meta = _collect_metadata(gen_llm)
    provider_log.append({"step": "generation", "call": "generate_initial_draft", **gen_meta})
    if gen_meta.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
    prof = analyzer.analyze_document(draft_0["content"], "draft_0")
    analysis_meta = _collect_metadata(lens_llm)
    provider_log.append({"step": "analysis", "call": "analyze_document", **analysis_meta})
    if analysis_meta.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
    draft_record = DraftRecord(
        version="draft_0",
        content=draft_0["content"],
        word_count=len(draft_0["content"].split()),
        profile=prof.dict(),
        diagnostics=None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    gen_cfg = config.get("generation", {})
    analysis_cfg = config.get("analysis", {})
    
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="baseline",
        provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        model=gen_meta.get("model", gen_cfg.get("model", "")),
        generation_provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        generation_model=gen_meta.get("model", gen_cfg.get("model", "")),
        analysis_provider=analysis_meta.get("provider", analysis_cfg.get("provider", "")),
        analysis_model=analysis_meta.get("model", analysis_cfg.get("model", "")),
        fallback_used=any_fallback,
        fallback_count=fallback_count,
        provider_log=provider_log,
        generation_config={"temperature": gen_cfg.get("temperature", 0.7), "max_output_tokens": gen_cfg.get("max_output_tokens", 1024)},
        analysis_mode=analysis_cfg.get("mode", "core"),
        core30_source=analysis_cfg.get("core30_source", "core30_approximation.json"),
        status="success",
        drafts=[draft_record],
        revision_history=[],
        metrics={},
        errors=[],
        started_at=start_time,
        completed_at=datetime.utcnow().isoformat() + "Z"
    )

def run_prompt_revision(prompt: Dict[str, Any], generator: NarrativeForgeGenerator, analyzer: NarrativeLensAnalyzer,
                        run_id: str, gen_llm: LLMProvider, lens_llm: LLMProvider, config: Dict[str, Any]) -> EvaluationRun:
    intent = WritingIntent(
        prompt=prompt["prompt"],
        genre=prompt["genre"],
        tone=prompt["tone"],
        pov=prompt["pov"],
        length=prompt["target_length"],
        constraints=prompt["required_facts"]
    )
    
    start_time = datetime.utcnow().isoformat() + "Z"
    provider_log = []
    fallback_count = 0
    any_fallback = False
    
    draft_0 = generator.generate_initial_draft(intent)
    gen_meta = _collect_metadata(gen_llm)
    provider_log.append({"step": "generation", "call": "generate_initial_draft", **gen_meta})
    if gen_meta.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
    prof_0 = analyzer.analyze_document(draft_0["content"], "draft_0")
    analysis_meta_0 = _collect_metadata(lens_llm)
    provider_log.append({"step": "analysis", "call": "analyze_document_draft_0", **analysis_meta_0})
    if analysis_meta_0.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
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
    
    res = gen_llm.get_structured_output(rev_prompt, schema)
    rev_meta = _collect_metadata(gen_llm)
    provider_log.append({"step": "revision", "call": "prompt_revision", **rev_meta})
    if rev_meta.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
    try:
        res_clean = res.strip()
        if res_clean.startswith("```json"):
            res_clean = res_clean[7:]
        if res_clean.endswith("```"):
            res_clean = res_clean[:-3]
        content_1 = json.loads(res_clean).get("revised_content", "")
    except Exception:
        content_1 = res  # fallback
        
    prof_1 = analyzer.analyze_document(content_1, "draft_1")
    analysis_meta_1 = _collect_metadata(lens_llm)
    provider_log.append({"step": "analysis", "call": "analyze_document_draft_1", **analysis_meta_1})
    if analysis_meta_1.get("fallback_used"):
        fallback_count += 1
        any_fallback = True
    
    draft_record_1 = DraftRecord(
        version="draft_1",
        content=content_1,
        word_count=len(content_1.split()),
        profile=prof_1.dict(),
        diagnostics=None,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    gen_cfg = config.get("generation", {})
    analysis_cfg = config.get("analysis", {})
    
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="prompt_revision",
        provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        model=gen_meta.get("model", gen_cfg.get("model", "")),
        generation_provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        generation_model=gen_meta.get("model", gen_cfg.get("model", "")),
        analysis_provider=analysis_meta_0.get("provider", analysis_cfg.get("provider", "")),
        analysis_model=analysis_meta_0.get("model", analysis_cfg.get("model", "")),
        fallback_used=any_fallback,
        fallback_count=fallback_count,
        provider_log=provider_log,
        generation_config={"temperature": gen_cfg.get("temperature", 0.7), "max_output_tokens": gen_cfg.get("max_output_tokens", 1024)},
        analysis_mode=analysis_cfg.get("mode", "core"),
        core30_source=analysis_cfg.get("core30_source", "core30_approximation.json"),
        status="success",
        drafts=[draft_record_0, draft_record_1],
        revision_history=[],
        metrics={},
        errors=[],
        started_at=start_time,
        completed_at=datetime.utcnow().isoformat() + "Z"
    )

def run_narrative_forge(prompt: Dict[str, Any], orchestrator: ForgeOrchestrator, run_id: str,
                        gen_llm: LLMProvider, lens_llm: LLMProvider, config: Dict[str, Any],
                        max_cycles: int = 3) -> EvaluationRun:
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
    
    # Collect cumulative provider metadata from both LLM instances
    gen_meta = _collect_metadata(gen_llm)
    analysis_meta = _collect_metadata(lens_llm)
    
    provider_log = []
    fallback_count = 0
    any_fallback = False
    
    # The orchestrator makes multiple calls; we track the last metadata from each provider
    if gen_meta:
        provider_log.append({"step": "forge_generation", **gen_meta})
        if gen_meta.get("fallback_used"):
            fallback_count += 1
            any_fallback = True
    if analysis_meta:
        provider_log.append({"step": "forge_analysis", **analysis_meta})
        if analysis_meta.get("fallback_used"):
            fallback_count += 1
            any_fallback = True
    
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
    
    gen_cfg = config.get("generation", {})
    analysis_cfg = config.get("analysis", {})
        
    return EvaluationRun(
        run_id=run_id,
        experiment_id="phase14",
        prompt_id=prompt["prompt_id"],
        system="narrative_forge",
        provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        model=gen_meta.get("model", gen_cfg.get("model", "")),
        generation_provider=gen_meta.get("provider", gen_cfg.get("provider", "")),
        generation_model=gen_meta.get("model", gen_cfg.get("model", "")),
        analysis_provider=analysis_meta.get("provider", analysis_cfg.get("provider", "")),
        analysis_model=analysis_meta.get("model", analysis_cfg.get("model", "")),
        fallback_used=any_fallback,
        fallback_count=fallback_count,
        provider_log=provider_log,
        generation_config={"temperature": gen_cfg.get("temperature", 0.7), "max_output_tokens": gen_cfg.get("max_output_tokens", 1024)},
        analysis_mode=analysis_cfg.get("mode", "core"),
        core30_source=analysis_cfg.get("core30_source", "core30_approximation.json"),
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
        
    # ========================================================
    # DUAL-BRAIN INITIALIZATION
    # ========================================================
    # Forge agent: GPT-OSS primary, Gemini fallback (for generation)
    # Lens agent: Gemini primary, GPT-OSS fallback (for analysis)
    # ========================================================
    
    gen_llm = LLMProvider(agent="forge")   # GPT-OSS 120B primary
    lens_llm = LLMProvider(agent="lens")   # Gemini primary
    
    tax_loader = TaxonomyLoader("data/storyscope/taxonomy.json", "data/storyscope/core30_approximation.json")
    taxonomy = tax_loader.load_taxonomy()
    core30 = tax_loader.load_core30()
    core30_selector = Core30Selector(core30)
    
    extractor = FeatureExtractor(taxonomy, lens_llm)  # Analysis uses Lens LLM (Gemini)
    
    lens = NarrativeLensAnalyzer(extractor, None, core30_selector, taxonomy)
    forge = NarrativeForgeGenerator(gen_llm)  # Generation uses Forge LLM (GPT-OSS)
    
    diag_engine = DiagnosticEngine(taxonomy)
    planner = RevisionPlanner(diag_engine, taxonomy)
    agent = RevisionAgent(gen_llm)  # Revision uses Forge LLM (GPT-OSS)
    effect_eval = RevisionEffectEvaluator(taxonomy)
    intent_eval = IntentPreservationEvaluator()
    qg = QualityGate()
    
    orchestrator = ForgeOrchestrator(forge, lens, core30_selector, diag_engine, planner, agent, effect_eval, intent_eval, qg, taxonomy)
    
    output_dir = os.path.join(config["output"]["directory"], datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(output_dir, exist_ok=True)
    
    run_file = os.path.join(output_dir, "runs.jsonl")
    
    print(f"=" * 60)
    print(f"PHASE 14A PILOT — DUAL-BRAIN ARCHITECTURE")
    print(f"Generation: {config['generation']['provider']} / {config['generation']['model']}")
    print(f"Analysis:   {config['analysis']['provider']} / {config['analysis']['model']}")
    print(f"Prompts:    {len(prompts)}")
    print(f"Systems:    {config['systems']}")
    print(f"Output:     {run_file}")
    print(f"=" * 60)
    
    for prompt in prompts:
        for system in config["systems"]:
            run_id = str(uuid.uuid4())
            print(f"\nRunning {system} for {prompt['prompt_id']} (Run ID: {run_id})")
            t0 = time.time()
            try:
                if system == "baseline":
                    run = run_baseline(prompt, forge, lens, run_id, gen_llm, lens_llm, config)
                elif system == "prompt_revision":
                    run = run_prompt_revision(prompt, forge, lens, run_id, gen_llm, lens_llm, config)
                elif system == "narrative_forge":
                    max_cycles = config.get("forge", {}).get("max_cycles", 3)
                    run = run_narrative_forge(prompt, orchestrator, run_id, gen_llm, lens_llm, config, max_cycles=max_cycles)
                else:
                    continue
                
                elapsed = time.time() - t0
                run.metrics["latency_seconds"] = round(elapsed, 2)
                
                # Print summary
                fb_tag = " [FALLBACK]" if run.fallback_used else ""
                print(f"  Status: {run.status} | Gen: {run.generation_provider}/{run.generation_model} | "
                      f"Analysis: {run.analysis_provider}/{run.analysis_model} | "
                      f"Latency: {elapsed:.1f}s{fb_tag}")
                    
                with open(run_file, "a", encoding="utf-8") as f:
                    f.write(run.model_dump_json() + "\n")
            except Exception as e:
                elapsed = time.time() - t0
                print(f"  FAILED {system} on {prompt['prompt_id']}: {str(e)}")
                gen_cfg = config.get("generation", {})
                analysis_cfg = config.get("analysis", {})
                failed_run = EvaluationRun(
                    run_id=run_id,
                    experiment_id="phase14",
                    prompt_id=prompt["prompt_id"],
                    system=system,
                    provider=gen_cfg.get("provider", ""),
                    model=gen_cfg.get("model", ""),
                    generation_provider=gen_cfg.get("provider", ""),
                    generation_model=gen_cfg.get("model", ""),
                    analysis_provider=analysis_cfg.get("provider", ""),
                    analysis_model=analysis_cfg.get("model", ""),
                    fallback_used=False,
                    fallback_count=0,
                    provider_log=[{"step": "error", "error": str(e)}],
                    generation_config={},
                    analysis_mode=analysis_cfg.get("mode", "core"),
                    core30_source=analysis_cfg.get("core30_source", ""),
                    status="failed",
                    drafts=[],
                    revision_history=[],
                    metrics={"latency_seconds": round(elapsed, 2)},
                    errors=[str(e)],
                    started_at="",
                    completed_at=datetime.utcnow().isoformat() + "Z"
                )
                with open(run_file, "a", encoding="utf-8") as f:
                    f.write(failed_run.model_dump_json() + "\n")

    print(f"\n{'=' * 60}")
    print(f"PILOT COMPLETE. Output: {run_file}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
