from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class DraftRecord(BaseModel):
    version: str
    content: str
    word_count: int
    profile: Optional[Dict[str, Any]] = None
    diagnostics: Optional[List[Dict[str, Any]]] = None
    timestamp: str

class RevisionHistoryRecord(BaseModel):
    cycle: int
    revision_plan: Dict[str, Any]
    revision_effect: Dict[str, Any]
    intent_preservation: Dict[str, Any]
    quality_gate: Dict[str, Any]
    timestamp: str

class EvaluationRun(BaseModel):
    run_id: str
    experiment_id: str
    prompt_id: str
    system: str
    provider: str
    model: str
    generation_config: Dict[str, Any]
    analysis_mode: str
    core30_source: str
    status: str
    drafts: List[DraftRecord]
    revision_history: List[RevisionHistoryRecord]
    metrics: Dict[str, Any]
    errors: List[str]
    started_at: str
    completed_at: str
