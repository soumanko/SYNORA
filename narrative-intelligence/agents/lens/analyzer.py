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
    
    def __init__(self, feature_extractor: FeatureExtractor, classifier: Any, core30_selector: Core30Selector, taxonomy: Dict[str, Any] = None):
        self.feature_extractor = feature_extractor
        self.classifier = classifier
        self.core30_selector = core30_selector
        self.taxonomy = taxonomy
        
    def analyze_document(self, document_id: str, document_text: str) -> NarrativeProfile:
        """
        Extracts features (Core30 or Full304) and runs classification to build a NarrativeProfile.
        """
        import os
        from core.taxonomy.schemas import FeatureValue
        
        mode = os.getenv("LENS_ANALYSIS_MODE", "full")
        
        if mode == "core" and self.taxonomy is not None:
            # Only extract core30 features
            core_ids = set(self.core30_selector.core30_features.keys())
            
            # Extract only the 30 core features using the extractor (assuming it's configured for it)
            # Actually, to make it clean, we'll temporarily swap the extractor's taxonomy or let extractor do all 304 
            # Wait, if we just swap the extractor's dimension_analyzers:
            from core.extraction.dimension_analyzer import FeatureExtractor
            core_taxonomy = {k: v for k, v in self.taxonomy.items() if k in core_ids}
            core_extractor = FeatureExtractor(core_taxonomy, self.feature_extractor.llm_provider)
            features = core_extractor.extract_all(document_text)
            
            # Fill remaining with unavailable
            extracted_ids = {f.feature_id for f in features}
            for k, v in self.taxonomy.items():
                if k not in extracted_ids:
                    features.append(FeatureValue(feature_id=k, value=None, confidence=0.0))
        else:
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
        
        # 4. Classify
        classification = None
        if mode == "core":
            # If classification requires the full encoded representation:
            # We don't have the full set, so we can't classify
            from core.taxonomy.schemas import ClassifierResult
            classification = ClassifierResult(
                human_probability=0.0,
                ai_probability=0.0,
                predicted_class="unavailable",
                model_version="unavailable",
                feature_set="full feature set required"
            )
        else:
            if self.classifier:
                classification = self.classifier.classify(full_feature_vector)
        
        # 5. Build Profile
        profile = NarrativeProfile(
            document_id=document_id,
            core30_features=core30_feature_vector,
            full304_features=full_feature_vector,
            classification=classification,
            diagnostics={"diagnostic_scope": "core_features"} if mode == "core" else {},
            metadata={
                "analysis_mode": mode,
                "feature_coverage": {
                    "analyzed": 30 if mode == "core" else 304,
                    "total": 304
                },
                "llm": getattr(self.feature_extractor.llm_provider, "last_metadata", {})
            }
        )
        
        return profile

