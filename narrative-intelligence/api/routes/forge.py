from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid

from core.taxonomy.taxonomy_loader import TaxonomyLoader
from core.analysis.core30 import Core30Selector
from core.llm_provider import LLMProvider
from core.extraction.dimension_analyzer import FeatureExtractor
from agents.lens.analyzer import NarrativeLensAnalyzer
from agents.forge.generator import NarrativeForgeGenerator, WritingIntent
from core.diagnostics.diagnostic_engine import DiagnosticEngine
from agents.forge.revision_planner import RevisionPlanner
from agents.forge.revision_agent import RevisionAgent
from core.evaluation.revision_effect import RevisionEffectEvaluator
from core.evaluation.intent_preservation import IntentPreservationEvaluator
from core.evaluation.quality_gate import QualityGate
from agents.forge.orchestrator import ForgeOrchestrator

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str
    genre: str
    tone: str
    pov: str
    length: int
    constraints: Optional[list] = []
    max_cycles: Optional[int] = 3

# Dependency initialization
taxonomy_loader = TaxonomyLoader(
    taxonomy_path="data/storyscope/taxonomy.json",
    core30_path="data/storyscope/core30_approximation.json"
)
try:
    taxonomy = taxonomy_loader.load_taxonomy()
    core30_features = taxonomy_loader.load_core30()
except FileNotFoundError:
    taxonomy = {}
    core30_features = []

core30_selector = Core30Selector(core30_features)
llm_provider = LLMProvider()
feature_extractor = FeatureExtractor(taxonomy, llm_provider=llm_provider)

lens_analyzer = NarrativeLensAnalyzer(
    feature_extractor=feature_extractor,
    classifier=None,
    core30_selector=core30_selector,
    taxonomy=taxonomy
)

forge_generator = NarrativeForgeGenerator(llm_provider)
diagnostic_engine = DiagnosticEngine(taxonomy)
revision_planner = RevisionPlanner(diagnostic_engine, taxonomy)
revision_agent = RevisionAgent(llm_provider)
revision_effect_evaluator = RevisionEffectEvaluator(taxonomy)
intent_preservation_evaluator = IntentPreservationEvaluator()
quality_gate = QualityGate()

orchestrator = ForgeOrchestrator(
    generator=forge_generator,
    lens_analyzer=lens_analyzer,
    core30_selector=core30_selector,
    diagnostic_engine=diagnostic_engine,
    revision_planner=revision_planner,
    revision_agent=revision_agent,
    revision_effect_evaluator=revision_effect_evaluator,
    intent_preservation_evaluator=intent_preservation_evaluator,
    quality_gate=quality_gate,
    taxonomy=taxonomy
)

@router.post("/generate")
def generate_story(req: GenerateRequest):
    """
    Executes the multi-cycle Narrative Forge loop using ForgeOrchestrator.
    """
    intent = WritingIntent(
        prompt=req.prompt,
        genre=req.genre,
        tone=req.tone,
        pov=req.pov,
        length=req.length,
        constraints=req.constraints
    )
    
    run_id = str(uuid.uuid4())
    state = orchestrator.execute_run(intent, max_cycles=req.max_cycles, run_id=run_id)
    
    # Format according to API contract
    final_version = state.versions[-1]
    
    return {
        "run_id": state.run_id,
        "status": state.status,
        "final": {
            "version": final_version.version,
            "content": final_version.content
        },
        "revision_history": [v.dict() for v in state.versions],
        "quality": state.revisions[-1].quality_report if state.revisions else {},
        "stop_reason": state.stop_reason,
        "metadata": state.metadata
    }
