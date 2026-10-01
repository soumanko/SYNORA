from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field

class FeatureType(str, Enum):
    BINARY = "binary"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    SCALE = "scale"
    MULTI_SELECT = "multi-select"

class Dimension(str, Enum):
    AGENTS = "Agents"
    SOCIAL_NETWORKS = "Social Networks"
    STYLE = "Style"
    PLOT = "Plot"
    SETTING = "Setting"
    EVENTS = "Events"
    REVELATION = "Revelation"
    SITUATEDNESS = "Situatedness"
    TEMPORAL_STRUCTURE = "Temporal Structure"
    PERSPECTIVE = "Perspective"

class Feature(BaseModel):
    id: str
    name: str
    dimension: Dimension
    aspect: Optional[str] = None
    question: str
    type: FeatureType
    values: Optional[List[Union[str, int, float]]] = None
    condition: Optional[str] = None
    detection_method: Optional[str] = None
    metadata: Optional[dict] = None

class Core30Feature(BaseModel):
    id: str
    name: str
    rank: int
    importance: float
    stability: float
    dimension: Dimension

class EvidenceSpan(BaseModel):
    text: str
    start: int
    end: int
    reason: str

class FeatureValue(BaseModel):
    feature_id: str
    value: Union[str, int, float, List[str], None]
    confidence: float = 1.0
    evidence: Optional[List[EvidenceSpan]] = None

class FeatureVector(BaseModel):
    document_id: str
    features: List[FeatureValue]
    metadata: Optional[dict] = None

class ClassifierResult(BaseModel):
    human_probability: float
    ai_probability: float
    predicted_class: str
    model_version: str
    feature_set: str
