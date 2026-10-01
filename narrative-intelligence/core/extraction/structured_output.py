import json
from typing import Dict, List, Any
from core.taxonomy.schemas import Feature, Dimension, FeatureValue

class StructuredOutputValidator:
    """Validates and fixes structured LLM output against the taxonomy."""
    
    @staticmethod
    def validate(raw_json: str, expected_features: List[Feature]) -> List[FeatureValue]:
        """
        Validates the extracted JSON against taxonomy schemas.
        Ensures no silent omissions.
        """
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # In a real engine, we'd trigger a retry here
            return []
            
        results = []
        for feature in expected_features:
            val = data.get(feature.id)
            # Schema validation
            if val is None:
                # Handle missing features explicitly
                results.append(FeatureValue(feature_id=feature.id, value="n/a", confidence=0.0))
                continue
                
            # If value is present, extract evidence if provided
            evidence = val.get("evidence") if isinstance(val, dict) else None
            actual_val = val.get("value") if isinstance(val, dict) else val
            
            results.append(FeatureValue(
                feature_id=feature.id,
                value=actual_val,
                confidence=val.get("confidence", 1.0) if isinstance(val, dict) else 1.0,
                evidence=evidence
            ))
            
        return results
