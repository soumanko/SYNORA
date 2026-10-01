from typing import List, Dict, Any

def extract_trajectory(revision_history: List[Dict[str, Any]], initial_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts the feature trajectory across revision cycles.
    """
    trajectories = []
    
    # Starting values (Draft 0)
    for feature_id, val in initial_profile.items():
        trajectories.append({
            "feature_id": feature_id,
            "cycle": 0,
            "value": val
        })
        
    # Subsequent values (Draft 1...N)
    for i, rev in enumerate(revision_history):
        # We need the profile *after* this revision
        # In this dataset schema, it might be in the next draft's profile
        pass # To be fully implemented by joining with drafts list
        
    return trajectories

def extract_full_trajectory(drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts trajectory from ordered list of drafts.
    """
    trajectories = []
    
    for cycle, draft in enumerate(drafts):
        profile = draft.get("profile", {})
        if not profile:
            continue
            
        for feature_id, val in profile.items():
            trajectories.append({
                "feature_id": feature_id,
                "cycle": cycle,
                "value": val
            })
            
    return trajectories
