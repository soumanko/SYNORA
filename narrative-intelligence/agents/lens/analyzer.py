from typing import Any, Dict
from core.taxonomy.schemas import FeatureVector
from core.extraction.dimension_analyzer import FeatureExtractor
from core.analysis.narrative_profile import NarrativeProfile
from core.analysis.core30 import Core30Selector

class NarrativeLensAnalyzer:
    """
    Core analyzer for the Narrative Lens agent.
    Handles document ingestion, feature extraction, and classification.
    """
    
    def __init__(self, feature_extractor: FeatureExtractor, classifier: Any, core30_selector: Core30Selector):
        self.feature_extractor = feature_extractor
        self.classifier = classifier
        self.core30_selector = core30_selector
        
    def analyze_document(self, document_id: str, document_text: str) -> NarrativeProfile:
        """
        Extracts features (Core30 or Full304) and runs classification to build a NarrativeProfile.
        """
        # 1. Chunking / Ingestion
        # 2. Extract features
        features = self.feature_extractor.extract_all(document_text)
        
        full_feature_vector = FeatureVector(
            document_id=document_id,
            features=features
        )
        
        # 3. Core30
        core30_features = self.core30_selector.filter_to_core(features)
        if not core30_features:
            raise ValueError("Core Feature Analysis failed: no core30 features extracted.")
            
        core30_feature_vector = FeatureVector(
            document_id=document_id,
            features=core30_features
        )
        
        # 4. Classify (where supported)
        # classification = self.classifier.classify(full_feature_vector)
        
        # 5. Build Profile
        profile = NarrativeProfile(
            document_id=document_id,
            core30_features=core30_feature_vector,
            full304_features=full_feature_vector,
            classification=None,
            diagnostics={},
            metadata={}
        )
        
        return profile

