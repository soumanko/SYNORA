import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.forge.generator import NarrativeForgeGenerator, WritingIntent
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

def main():
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        return
        
    print("=" * 70)
    print("PHASE 13 REAL-PROVIDER TEST: FORGE ORCHESTRATOR")
    print("=" * 70)
    
    # Init dependencies
    tax_loader = TaxonomyLoader(
        "data/storyscope/taxonomy.json",
        "data/storyscope/core30_approximation.json"
    )
    taxonomy = tax_loader.load_taxonomy()
    core30 = tax_loader.load_core30()
    core30_selector = Core30Selector(core30)
    
    llm = LLMProvider()
    extractor = FeatureExtractor(taxonomy, llm)
    
    lens = NarrativeLensAnalyzer(
        feature_extractor=extractor,
        classifier=None,
        core30_selector=core30_selector,
        taxonomy=taxonomy
    )
    
    forge = NarrativeForgeGenerator(llm)
    diag_engine = DiagnosticEngine(taxonomy)
    planner = RevisionPlanner(diag_engine, taxonomy)
    agent = RevisionAgent(llm)
    effect_eval = RevisionEffectEvaluator(taxonomy)
    intent_eval = IntentPreservationEvaluator()
    qg = QualityGate()
    
    orchestrator = ForgeOrchestrator(
        generator=forge,
        lens_analyzer=lens,
        core30_selector=core30_selector,
        diagnostic_engine=diag_engine,
        revision_planner=planner,
        revision_agent=agent,
        revision_effect_evaluator=effect_eval,
        intent_preservation_evaluator=intent_eval,
        quality_gate=qg,
        taxonomy=taxonomy
    )
    
    intent = WritingIntent(
        prompt="A very short 50-word story about a mysterious locked door.",
        genre="mystery",
        tone="suspenseful",
        pov="third person limited",
        length=50
    )
    
    os.environ["LENS_ANALYSIS_MODE"] = "core"
    try:
        state = orchestrator.execute_run(intent, max_cycles=3, run_id="real_test_1")
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
            return
        raise e
        
    print("=" * 70)
    print("RUN COMPLETED")
    print("=" * 70)
    print(f"Status: {state.status}")
    print(f"Stop Reason: {state.stop_reason}")
    print(f"Total Versions: {len(state.versions)}")
    print(f"Total Revisions: {len(state.revisions)}")
    
    if state.revisions:
        final_rep = state.revisions[-1]
        print("\nLast Quality Gate Decision:", final_rep.quality_report.get("decision"))
        print("Last Target Achievement:", final_rep.quality_report.get("checks", {}).get("target_achievement", {}).get("status"))
        print("Last Intent Preservation:", final_rep.intent_preservation.get("status"))
        
    print("\nFinal Draft Content:")
    print("-" * 30)
    print(state.versions[-1].content)
    print("-" * 30)

if __name__ == "__main__":
    main()
