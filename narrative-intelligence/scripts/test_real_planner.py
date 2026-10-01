"""
Real-provider test for the new Feature-Aware Revision Planning.
Runs a short Forge generation and planning cycle in Core mode.
"""
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

def main():
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        return
        
    print("=" * 70)
    print("PHASE 11 REAL-PROVIDER TEST: REVISION PLANNER")
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
    
    intent = WritingIntent(
        prompt="A very short 50-word story about a mysterious locked door.",
        genre="mystery",
        tone="suspenseful",
        pov="third person limited",
        length=50
    )
    
    print("1. Generating Draft 0...")
    draft_0 = forge.generate_initial_draft(intent)
    
    print("2. Analyzing Draft 0 (Core Mode)...")
    os.environ["LENS_ANALYSIS_MODE"] = "core"
    try:
        profile = lens.analyze_document(draft_0["draft_id"], draft_0["content"])
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
            return
        raise e
        
    print("3. Generating Diagnostics...")
    ref_profile = {f.id: "Expected Norm" for f in core30}
    deviations = core30_selector.analyze_deviation(profile.core30_features.features, ref_profile)
    diags = diag_engine.diagnose_deviations(deviations)
    
    print("4. Creating Revision Plan...")
    plan = planner.create_revision_plan(diags, intent)
    
    print("=" * 70)
    print("PHASE 12 METRICS")
    print("=" * 70)
    total_diags = len(diags)
    actionable_diags = [d for d in diags if d.actionability == "actionable"]
    informational_diags = [d for d in diags if d.actionability == "informational"]
    
    print(f"Total Diagnostics: {total_diags}")
    print(f"Actionable Diagnostics: {len(actionable_diags)}")
    print(f"Informational Diagnostics: {len(informational_diags)}")
    print(f"Valid Revision Targets Generated: {len(plan.get('interventions', []))}")
    
    rejected = len(actionable_diags) - len(plan.get('interventions', []))
    if rejected > 0 and len(actionable_diags) > 3:
        # Planner caps at 3 targets
        rejected = len(actionable_diags) - 3 if len(plan.get('interventions', [])) == 3 else rejected
    
    print(f"Rejected Actionable Diagnostics: {rejected}")
    if rejected > 0:
        print("Reasons for Rejection: Invalid taxonomy operations or exceeded max target count (3).")
    
    print("\n=" * 70)
    print("REVISION TARGETS")
    print("=" * 70)
    if not plan["interventions"]:
        print("No actionable targets found.")
    else:
        for t in plan["interventions"]:
            print(f"Target: {t['target']['feature_name']} ({t['target']['feature_id']})")
            print(f"Type: {t['target']['feature_type']}")
            print(f"Operation: {t['operation']}")
            if t['target_value']:
                print(f"Target Value: {t['target_value']}")
            if t['current_value']:
                print(f"Current Value: {t['current_value']}")
            print(f"Instruction: {t['revision_instruction']}\n")

if __name__ == "__main__":
    main()
