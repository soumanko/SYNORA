from typing import Dict, Any

def feature_distance(val1: Any, val2: Any, feature_type: str) -> float:
    """
    Computes type-aware distance between two feature values.
    """
    if val1 is None or val2 is None:
        return 0.0 # Cannot compute
        
    if feature_type == "SCALE":
        try:
            return abs(float(val2) - float(val1))
        except (ValueError, TypeError):
            return 1.0 if val1 != val2 else 0.0
            
    elif feature_type == "ORDINAL":
        # Simplified: assumes values are numeric or map to numeric
        try:
            return abs(float(val2) - float(val1))
        except (ValueError, TypeError):
            return 1.0 if val1 != val2 else 0.0
            
    elif feature_type == "CATEGORICAL":
        return 0.0 if str(val1) == str(val2) else 1.0
        
    elif feature_type == "MULTI_SELECT":
        set1 = set(val1) if isinstance(val1, list) else {val1}
        set2 = set(val2) if isinstance(val2, list) else {val2}
        union = set1.union(set2)
        if not union:
            return 0.0
        intersection = set1.intersection(set2)
        return 1.0 - (len(intersection) / len(union))
        
    elif feature_type == "BINARY":
        return 0.0 if bool(val1) == bool(val2) else 1.0
        
    return 0.0 if val1 == val2 else 1.0

def calculate_profile_distance(profile1: Dict[str, Any], profile2: Dict[str, Any], taxonomy: Dict[str, Any]) -> float:
    """
    Calculates the total distance between two profiles.
    """
    total_distance = 0.0
    common_keys = set(profile1.keys()).intersection(set(profile2.keys()))
    
    for key in common_keys:
        val1 = profile1[key]
        val2 = profile2[key]
        feature_type = taxonomy.get(key, {}).type if hasattr(taxonomy.get(key, {}), "type") else getattr(taxonomy.get(key, {}), "type", "CATEGORICAL")
        if isinstance(feature_type, str):
             ftype_str = feature_type.split('.')[-1]
        else:
             ftype_str = feature_type.name if hasattr(feature_type, "name") else "CATEGORICAL"
        
        total_distance += feature_distance(val1, val2, ftype_str)
        
    return total_distance
