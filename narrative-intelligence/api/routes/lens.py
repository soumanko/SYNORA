from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from core.analysis.narrative_profile import NarrativeProfile
from agents.lens.analyzer import NarrativeLensAnalyzer
from core.extraction.dimension_analyzer import FeatureExtractor
from core.taxonomy.taxonomy_loader import TaxonomyLoader
from core.analysis.core30 import Core30Selector

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str
    document_id: str

class AnalyzeResponse(BaseModel):
    status: str
    narrative_profile: Optional[NarrativeProfile] = None
    executive_summary: Optional[str] = None
    message: Optional[str] = None

# Initialize dependencies (in a real app, use dependency injection)
taxonomy_loader = TaxonomyLoader(
    taxonomy_path="data/storyscope/taxonomy.json",
    core30_path="data/storyscope/core30_approximation.json"
)
taxonomy = taxonomy_loader.load_taxonomy()
core30_features = taxonomy_loader.load_core30()
core30_selector = Core30Selector(core30_features)

# The extractor needs to be functional. Currently it's a placeholder.
feature_extractor = FeatureExtractor(taxonomy, llm_provider=None)

analyzer = NarrativeLensAnalyzer(
    feature_extractor=feature_extractor,
    classifier=None,
    core30_selector=core30_selector
)

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_document(req: AnalyzeRequest):
    """
    Executes the Narrative Lens pipeline:
    Parse -> Chunk -> 304 Analyzer -> Core30 -> Classify -> Narrative Profile
    """
    try:
        profile = analyzer.analyze_document(document_id=req.document_id, document_text=req.text)
        return AnalyzeResponse(
            status="success",
            narrative_profile=profile,
            executive_summary="Generated profile successfully."
        )
    except Exception as e:
        return AnalyzeResponse(
            status="failed",
            message=str(e)
        )
