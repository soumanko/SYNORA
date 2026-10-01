from typing import List, Dict, Any
from evaluation.metrics.feature_distance import calculate_profile_distance

def calculate_diversity(profiles: List[Dict[str, Any]], taxonomy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates pairwise Core30 distance between a set of output profiles for the same prompt.
    """
    if len(profiles) < 2:
        return {
            "mean_pairwise_distance": 0.0,
            "median_pairwise_distance": 0.0,
            "valid_comparisons": 0
        }
        
    distances = []
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            dist = calculate_profile_distance(profiles[i], profiles[j], taxonomy)
            distances.append(dist)
            
    distances.sort()
    mean_dist = sum(distances) / len(distances)
    
    mid = len(distances) // 2
    if len(distances) % 2 == 0:
        median_dist = (distances[mid - 1] + distances[mid]) / 2.0
    else:
        median_dist = distances[mid]
        
    return {
        "mean_pairwise_distance": mean_dist,
        "median_pairwise_distance": median_dist,
        "valid_comparisons": len(distances)
    }
