from typing import List, Dict, Any

def calculate_incidental_movement(revision_plans: List[Dict[str, Any]], profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates incidental movement outside explicitly targeted features.
    """
    incidental_changes = []
    
    total_targeted = 0
    total_incidental = 0
    total_unchanged = 0
    total_unavailable = 0
    
    for i, plan in enumerate(revision_plans):
        before_profile = profiles[i]
        after_profile = profiles[i+1]
        
        interventions = plan.get("interventions", [])
        targeted_features = {inv.get("feature_id") for inv in interventions if inv.get("feature_id")}
        
        all_features = set(before_profile.keys()).union(set(after_profile.keys()))
        
        for fid in all_features:
            before_val = before_profile.get(fid)
            after_val = after_profile.get(fid)
            
            if before_val is None or after_val is None:
                total_unavailable += 1
                continue
                
            is_targeted = fid in targeted_features
            
            if before_val != after_val:
                if is_targeted:
                    total_targeted += 1
                else:
                    total_incidental += 1
                    incidental_changes.append({
                        "feature_id": fid,
                        "before": before_val,
                        "after": after_val,
                        "cycle": i + 1
                    })
            else:
                total_unchanged += 1
                
    return {
        "targeted_changes": total_targeted,
        "incidental_changes": total_incidental,
        "unchanged_features": total_unchanged,
        "unavailable_features": total_unavailable,
        "incidental_change_rate": (total_incidental / (total_incidental + total_unchanged + total_targeted)) if (total_incidental + total_unchanged + total_targeted) > 0 else 0,
        "details": incidental_changes
    }
