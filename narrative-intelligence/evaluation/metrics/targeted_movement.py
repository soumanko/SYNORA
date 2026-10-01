from typing import List, Dict, Any

def calculate_targeted_movement(revision_plans: List[Dict[str, Any]], profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates the targeted movement for a sequence of revisions.
    revision_plans: List of revision plans applied (len N)
    profiles: List of profiles (Draft 0, Draft 1, ... Draft N) (len N+1)
    """
    movements = []
    achieved_count = 0
    total_measurable = 0
    
    for i, plan in enumerate(revision_plans):
        before_profile = profiles[i]
        after_profile = profiles[i+1]
        
        interventions = plan.get("interventions", [])
        for intervention in interventions:
            feature_id = intervention.get("feature_id")
            if not feature_id:
                continue
                
            op = intervention.get("op")
            target_value = intervention.get("target_value")
            
            before_val = before_profile.get(feature_id)
            after_val = after_profile.get(feature_id)
            
            # Simple assessment for numerical features
            # Categorical/ordinal require more complex distance functions
            achieved = False
            measurable = False
            change = None
            
            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                measurable = True
                change = after_val - before_val
                if op == "increase" and change > 0:
                    achieved = True
                elif op == "decrease" and change < 0:
                    achieved = True
                elif op == "preserve" and change == 0:
                    achieved = True
                    
            if measurable:
                total_measurable += 1
                if achieved:
                    achieved_count += 1
                    
            movements.append({
                "feature_id": feature_id,
                "operation": op,
                "target_value": target_value,
                "before": before_val,
                "after": after_val,
                "change": change,
                "target_achieved": "achieved" if achieved else ("not_achieved" if measurable else "not_measurable")
            })
            
    return {
        "interventions": movements,
        "total_targeted": len(movements),
        "total_measurable": total_measurable,
        "achieved_count": achieved_count,
        "target_achievement_rate": (achieved_count / total_measurable) if total_measurable > 0 else 0
    }
