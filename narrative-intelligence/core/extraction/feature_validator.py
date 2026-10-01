"""
FeatureValidator: Post-extraction validation of FeatureValues against
the StoryScope taxonomy.

Ensures every non-null categorical/multi-select/ordinal/scale/binary
FeatureValue contains a value from the taxonomy's defined value set.

Invalid values are set to None with a validation diagnostic.
No silent acceptance of free-text values.
No fabricated semantic mappings.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from core.taxonomy.schemas import Feature, FeatureType, FeatureValue


class ValidationResult:
    """Result of validating a single FeatureValue against the taxonomy."""
    
    def __init__(
        self,
        feature_id: str,
        valid: bool,
        normalized_value: Any,
        raw_value: Any = None,
        error: Optional[str] = None,
        invalid_items: Optional[List[str]] = None,
    ):
        self.feature_id = feature_id
        self.valid = valid
        self.normalized_value = normalized_value
        self.raw_value = raw_value
        self.error = error
        self.invalid_items = invalid_items or []
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "feature_id": self.feature_id,
            "valid": self.valid,
            "normalized_value": self.normalized_value,
        }
        if not self.valid:
            result["raw_value"] = self.raw_value
            result["error"] = self.error
            if self.invalid_items:
                result["invalid_items"] = self.invalid_items
        return result


class FeatureValidator:
    """
    Validates extracted FeatureValues against the loaded StoryScope taxonomy.
    
    Uses the taxonomy as the sole source of truth for allowed values.
    Does NOT hardcode any feature value lists.
    """
    
    def __init__(self, taxonomy: Dict[str, Feature]):
        """
        Args:
            taxonomy: Dict mapping feature_id -> Feature schema object.
        """
        self.taxonomy = taxonomy
        # Pre-compute normalized allowed value sets for fast lookup
        self._allowed_values: Dict[str, set] = {}
        for fid, feature in taxonomy.items():
            if feature.values:
                self._allowed_values[fid] = {
                    self._normalize_value(str(v)) for v in feature.values
                }
            else:
                self._allowed_values[fid] = set()
    
    @staticmethod
    def _normalize_value(v: str) -> str:
        """Normalizes a value string for comparison (lowercase, strip whitespace)."""
        return v.strip().lower()
    
    def validate_feature(self, feature_value: FeatureValue) -> ValidationResult:
        """
        Validates a single FeatureValue against its taxonomy definition.
        
        Returns a ValidationResult with the normalized value or None if invalid.
        """
        fid = feature_value.feature_id
        raw = feature_value.value
        
        # Feature not in taxonomy — cannot validate
        if fid not in self.taxonomy:
            return ValidationResult(
                feature_id=fid,
                valid=False,
                normalized_value=None,
                raw_value=raw,
                error="feature_not_in_taxonomy"
            )
        
        feature_def = self.taxonomy[fid]
        allowed = self._allowed_values.get(fid, set())
        
        # None / "n/a" values pass through as unavailable
        if raw is None or (isinstance(raw, str) and raw.strip().lower() in ("n/a", "", "null", "none")):
            return ValidationResult(
                feature_id=fid,
                valid=True,
                normalized_value=None,
                raw_value=raw,
            )
        
        ftype = feature_def.type
        
        if ftype == FeatureType.CATEGORICAL:
            return self._validate_categorical(fid, raw, allowed)
        elif ftype == FeatureType.BINARY:
            return self._validate_binary(fid, raw, allowed)
        elif ftype == FeatureType.MULTI_SELECT:
            return self._validate_multi_select(fid, raw, allowed)
        elif ftype == FeatureType.SCALE:
            return self._validate_scale(fid, raw, feature_def)
        elif ftype == FeatureType.ORDINAL:
            return self._validate_ordinal(fid, raw, allowed)
        else:
            return ValidationResult(
                feature_id=fid,
                valid=False,
                normalized_value=None,
                raw_value=raw,
                error=f"unknown_feature_type: {ftype}"
            )
    
    def _validate_categorical(self, fid: str, raw: Any, allowed: set) -> ValidationResult:
        """Categorical: value must be exactly one of the allowed values."""
        if not isinstance(raw, str):
            return ValidationResult(
                feature_id=fid, valid=False, normalized_value=None,
                raw_value=raw, error="categorical_value_must_be_string"
            )
        normalized = self._normalize_value(raw)
        if normalized in allowed:
            return ValidationResult(feature_id=fid, valid=True, normalized_value=raw)
        return ValidationResult(
            feature_id=fid, valid=False, normalized_value=None,
            raw_value=raw, error="value_not_in_taxonomy"
        )
    
    def _validate_binary(self, fid: str, raw: Any, allowed: set) -> ValidationResult:
        """Binary: value must be one of the defined binary values."""
        if not isinstance(raw, str):
            raw_str = str(raw)
        else:
            raw_str = raw
        normalized = self._normalize_value(raw_str)
        if normalized in allowed:
            return ValidationResult(feature_id=fid, valid=True, normalized_value=raw_str)
        return ValidationResult(
            feature_id=fid, valid=False, normalized_value=None,
            raw_value=raw, error="value_not_in_taxonomy"
        )
    
    def _validate_multi_select(self, fid: str, raw: Any, allowed: set) -> ValidationResult:
        """
        Multi-select: each item must be in the allowed set.
        Valid items are preserved, invalid items are removed and recorded.
        If all items are invalid, the feature value is None.
        """
        if isinstance(raw, str):
            # LLM sometimes returns a single string instead of a list
            raw = [raw]
        if not isinstance(raw, list):
            return ValidationResult(
                feature_id=fid, valid=False, normalized_value=None,
                raw_value=raw, error="multi_select_value_must_be_list"
            )
        
        valid_items = []
        invalid_items = []
        for item in raw:
            item_str = str(item)
            if self._normalize_value(item_str) in allowed:
                valid_items.append(item_str)
            else:
                invalid_items.append(item_str)
        
        if not valid_items and invalid_items:
            return ValidationResult(
                feature_id=fid, valid=False, normalized_value=None,
                raw_value=raw, error="all_values_invalid",
                invalid_items=invalid_items
            )
        elif invalid_items:
            # Partial validity: keep valid, remove invalid
            return ValidationResult(
                feature_id=fid, valid=True, normalized_value=valid_items,
                raw_value=raw, error=None,
                invalid_items=invalid_items
            )
        else:
            return ValidationResult(feature_id=fid, valid=True, normalized_value=valid_items)
    
    def _validate_scale(self, fid: str, raw: Any, feature_def: Feature) -> ValidationResult:
        """
        Scale: value must be numeric and within the defined bounds.
        Taxonomy scale values are typically ["1","2","3","4","5"] or [1,2,3,4,5].
        """
        try:
            if isinstance(raw, str):
                # Handle "3 - description" format
                num_str = raw.strip().split(" ")[0].split("-")[0].strip()
                num_val = float(num_str)
            elif isinstance(raw, (int, float)):
                num_val = float(raw)
            else:
                return ValidationResult(
                    feature_id=fid, valid=False, normalized_value=None,
                    raw_value=raw, error="scale_value_not_numeric"
                )
        except (ValueError, IndexError):
            return ValidationResult(
                feature_id=fid, valid=False, normalized_value=None,
                raw_value=raw, error="scale_value_not_numeric"
            )
        
        # Extract numeric bounds from taxonomy values
        if feature_def.values:
            try:
                bounds = [float(str(v).strip().split(" ")[0].split("-")[0].strip()) for v in feature_def.values]
                min_val = min(bounds)
                max_val = max(bounds)
                if num_val < min_val or num_val > max_val:
                    return ValidationResult(
                        feature_id=fid, valid=False, normalized_value=None,
                        raw_value=raw, error=f"scale_value_out_of_range: {num_val} not in [{min_val}, {max_val}]"
                    )
            except (ValueError, TypeError):
                pass  # Can't determine bounds, allow the numeric value
        
        return ValidationResult(feature_id=fid, valid=True, normalized_value=num_val)
    
    def _validate_ordinal(self, fid: str, raw: Any, allowed: set) -> ValidationResult:
        """
        Ordinal: value must match one of the defined ordinal categories.
        """
        if not isinstance(raw, str):
            raw_str = str(raw)
        else:
            raw_str = raw
        normalized = self._normalize_value(raw_str)
        if normalized in allowed:
            return ValidationResult(feature_id=fid, valid=True, normalized_value=raw_str)
        
        # Also try matching just the numeric prefix (e.g., "3" matching "3 - description")
        try:
            num_prefix = raw_str.strip().split(" ")[0].split("-")[0].strip()
            for allowed_val in allowed:
                if allowed_val.startswith(num_prefix + " ") or allowed_val == num_prefix:
                    return ValidationResult(feature_id=fid, valid=True, normalized_value=raw_str)
        except (ValueError, IndexError):
            pass
        
        return ValidationResult(
            feature_id=fid, valid=False, normalized_value=None,
            raw_value=raw, error="value_not_in_taxonomy"
        )
    
    def validate_feature_vector(
        self, feature_values: List[FeatureValue]
    ) -> Tuple[List[FeatureValue], Dict[str, Any]]:
        """
        Validates an entire list of FeatureValues and returns:
        1. A list of validated FeatureValues (invalid values set to None)
        2. Extraction validation metadata/diagnostics
        """
        validated = []
        diagnostics = []
        total = len(feature_values)
        valid_count = 0
        invalid_count = 0
        missing_count = 0
        
        for fv in feature_values:
            result = self.validate_feature(fv)
            
            if result.normalized_value is None and fv.value is not None and not result.valid:
                # Invalid value: set to None, record diagnostic
                validated.append(FeatureValue(
                    feature_id=fv.feature_id,
                    value=None,
                    confidence=0.0,
                    evidence=fv.evidence
                ))
                invalid_count += 1
                diagnostics.append(result.to_dict())
            elif result.valid and result.normalized_value is not None:
                # Valid value: use normalized
                validated.append(FeatureValue(
                    feature_id=fv.feature_id,
                    value=result.normalized_value,
                    confidence=fv.confidence,
                    evidence=fv.evidence
                ))
                valid_count += 1
                if result.invalid_items:
                    diagnostics.append(result.to_dict())
            else:
                # Missing/unavailable
                validated.append(FeatureValue(
                    feature_id=fv.feature_id,
                    value=None,
                    confidence=0.0,
                    evidence=fv.evidence
                ))
                missing_count += 1
        
        metadata = {
            "extraction_validation": {
                "total_features_attempted": total,
                "valid_features": valid_count,
                "invalid_features": invalid_count,
                "missing_features": missing_count,
            },
            "invalid_value_diagnostics": diagnostics
        }
        
        return validated, metadata
