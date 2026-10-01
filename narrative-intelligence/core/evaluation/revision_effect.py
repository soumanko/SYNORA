"""
RevisionEffectEvaluator: Compares two NarrativeProfiles to measure
targeted vs incidental feature movement after a revision cycle.

Feature types in the StoryScope taxonomy:
  - scale/ordinal: numeric values → compute numeric delta
  - categorical: single string → report changed/unchanged
  - multi-select: list of strings → report set-based changes (added/removed)
  - binary: single value → report changed/unchanged

This evaluator does NOT invent thresholds or fabricate scores.
It reports observed measurements and clearly marks unavailable comparisons.
"""

from typing import Dict, Any, List, Optional, Union
from core.analysis.narrative_profile import NarrativeProfile
from core.taxonomy.schemas import FeatureValue, FeatureType


class FeatureChange:
    """Represents a single feature's observed change between two profiles."""
    
    def __init__(
        self,
        feature_id: str,
        feature_name: str,
        feature_type: str,
        value_before: Any,
        value_after: Any,
        is_targeted: bool,
        operation: Optional[str] = None,
        target_value: Optional[Any] = None
    ):
        self.feature_id = feature_id
        self.feature_name = feature_name
        self.feature_type = feature_type
        self.value_before = value_before
        self.value_after = value_after
        self.is_targeted = is_targeted
        self.operation = operation
        self.target_value = target_value
        
    def compute_delta(self) -> Dict[str, Any]:
        """
        Computes the observed delta based on feature type.
        Returns a dict with measurement or 'unavailable' status.
        """
        if self.value_before is None or self.value_after is None:
            return {
                "status": "unavailable",
                "reason": "one or both values are None"
            }
        
        # Scale / ordinal: attempt numeric delta
        if self.feature_type in ("scale", "ordinal"):
            try:
                num_before = self._extract_numeric(self.value_before)
                num_after = self._extract_numeric(self.value_after)
                if num_before is not None and num_after is not None:
                    delta = num_after - num_before
                    return {
                        "status": "measured",
                        "comparison_type": "numeric",
                        "before": num_before,
                        "after": num_after,
                        "delta": delta,
                        "direction_observed": "increase" if delta > 0 else ("decrease" if delta < 0 else "unchanged"),
                        "target_match": self._check_target_match(delta=delta)
                    }
                else:
                    return {
                        "status": "unavailable",
                        "reason": "could not extract numeric values from scale/ordinal feature",
                        "before_raw": self.value_before,
                        "after_raw": self.value_after
                    }
            except (ValueError, TypeError):
                return {
                    "status": "unavailable",
                    "reason": "numeric conversion failed",
                    "before_raw": self.value_before,
                    "after_raw": self.value_after
                }
        
        # Multi-select: set-based comparison
        if self.feature_type == "multi-select" or self.feature_type == "multi_select":
            before_set = set(self.value_before) if isinstance(self.value_before, list) else set([self.value_before]) if self.value_before else set()
            after_set = set(self.value_after) if isinstance(self.value_after, list) else set([self.value_after]) if self.value_after else set()
            added = after_set - before_set
            removed = before_set - after_set
            retained = before_set & after_set
            changed = bool(added or removed)
            return {
                "status": "measured",
                "comparison_type": "set",
                "before": sorted(before_set),
                "after": sorted(after_set),
                "added": sorted(added),
                "removed": sorted(removed),
                "retained": sorted(retained),
                "changed": changed,
                "target_match": self._check_target_match(added=added, removed=removed)
            }
        
        # Categorical / binary: equality check
        if self.feature_type in ("categorical", "binary"):
            changed = self.value_before != self.value_after
            return {
                "status": "measured",
                "comparison_type": "categorical",
                "before": self.value_before,
                "after": self.value_after,
                "changed": changed,
                "target_match": self._check_target_match(after_val=self.value_after)
            }
        
        # Unknown type
        return {
            "status": "unavailable",
            "reason": f"unsupported feature type: {self.feature_type}"
        }
    
    def _extract_numeric(self, value: Any) -> Optional[float]:
        """Extracts a numeric value from potentially string-encoded scale values."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Handle "3 - description" format
            parts = value.strip().split(" ")
            try:
                return float(parts[0])
            except (ValueError, IndexError):
                return None
        return None
    
    def _check_target_match(self, delta: float = None, added: set = None, removed: set = None, after_val: Any = None) -> Union[bool, str]:
        """Checks if the observed change matches the planned operation and target value."""
        if not self.is_targeted or not self.operation:
            return None
            
        op = self.operation
        
        if op == "increase" and delta is not None:
            return delta > 0
        elif op == "decrease" and delta is not None:
            return delta < 0
        elif op == "preserve":
            if delta is not None:
                return abs(delta) < 0.001
            elif added is not None and removed is not None:
                return len(added) == 0 and len(removed) == 0
            else:
                return self.value_before == self.value_after
        elif op == "set":
            if self.target_value is not None and after_val is not None:
                return str(self.target_value).lower() == str(after_val).lower()
        elif op == "add" and added is not None:
            if self.target_value:
                return any(str(self.target_value).lower() == str(a).lower() for a in added)
        elif op == "remove" and removed is not None:
            if self.target_value:
                return any(str(self.target_value).lower() == str(r).lower() for r in removed)
                
        return "comparison_unavailable"
    
    def to_dict(self) -> Dict[str, Any]:
        delta = self.compute_delta()
        return {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "feature_type": self.feature_type,
            "is_targeted": self.is_targeted,
            "operation": self.operation,
            "target_value": self.target_value,
            **delta
        }


class RevisionEffectEvaluator:
    """
    Compares two NarrativeProfiles to evaluate the effect of a revision cycle.
    
    Separates targeted changes (features explicitly in the revision plan)
    from incidental changes (features that shifted as a side effect).
    
    Does NOT fabricate measurements. Reports 'unavailable' when comparison
    is not meaningful for a given feature type.
    """
    
    def __init__(self, taxonomy: Dict[str, Any] = None):
        """
        Args:
            taxonomy: Dict mapping feature_id -> Feature schema object.
                      Used to look up feature type and name.
        """
        self.taxonomy = taxonomy or {}
    
    def evaluate(
        self,
        profile_before: NarrativeProfile,
        profile_after: NarrativeProfile,
        revision_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares two profiles and produces a structured revision effect report.
        """
        # Extract targeted feature IDs from the revision plan
        targeted_ids = set()
        target_operations = {}
        target_values = {}
        for intervention in revision_plan.get("interventions", []):
            fid = intervention.get("target", {}).get("feature_id", "")
            targeted_ids.add(fid)
            target_operations[fid] = intervention.get("operation", None)
            target_values[fid] = intervention.get("target_value", None)
        
        # Build lookup maps: feature_id -> FeatureValue
        before_map = {fv.feature_id: fv for fv in profile_before.core30_features.features}
        after_map = {fv.feature_id: fv for fv in profile_after.core30_features.features}
        
        all_feature_ids = set(before_map.keys()) | set(after_map.keys())
        
        targeted_changes = []
        incidental_changes = []
        unchanged_features = []
        
        for fid in sorted(all_feature_ids):
            fv_before = before_map.get(fid)
            fv_after = after_map.get(fid)
            
            is_targeted = fid in targeted_ids
            
            # Look up feature type from taxonomy
            feature_type = "unknown"
            feature_name = fid
            if fid in self.taxonomy:
                tax_feature = self.taxonomy[fid]
                feature_type = tax_feature.type.value if hasattr(tax_feature.type, 'value') else str(tax_feature.type)
                feature_name = tax_feature.name
            
            change = FeatureChange(
                feature_id=fid,
                feature_name=feature_name,
                feature_type=feature_type,
                value_before=fv_before.value if fv_before else None,
                value_after=fv_after.value if fv_after else None,
                is_targeted=is_targeted,
                operation=target_operations.get(fid),
                target_value=target_values.get(fid)
            )
            
            delta = change.compute_delta()
            change_dict = change.to_dict()
            
            # Classify: targeted, incidental, or unchanged
            if is_targeted:
                targeted_changes.append(change_dict)
            elif delta.get("status") == "measured":
                is_changed = delta.get("changed", False) or delta.get("delta", 0) != 0
                if is_changed:
                    incidental_changes.append(change_dict)
                else:
                    unchanged_features.append(change_dict)
            else:
                unchanged_features.append(change_dict)
        
        # Compute target success summary
        target_results = []
        for tc in targeted_changes:
            target_results.append({
                "feature_id": tc["feature_id"],
                "target_match": tc.get("target_match", "comparison_unavailable")
            })
        
        return {
            "targeted_changes": targeted_changes,
            "incidental_changes": incidental_changes,
            "unchanged_features": unchanged_features,
            "target_success": target_results,
            "summary": {
                "total_features_compared": len(all_feature_ids),
                "targeted_count": len(targeted_changes),
                "incidental_count": len(incidental_changes),
                "unchanged_count": len(unchanged_features)
            }
        }
