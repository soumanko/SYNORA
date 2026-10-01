import pytest
from evaluation.metrics.feature_distance import feature_distance
from evaluation.metrics.targeted_movement import calculate_targeted_movement

def test_feature_distance_categorical():
    assert feature_distance("apple", "apple", "CATEGORICAL") == 0.0
    assert feature_distance("apple", "orange", "CATEGORICAL") == 1.0

def test_feature_distance_scale():
    assert feature_distance(2.0, 3.5, "SCALE") == 1.5
    assert feature_distance(2, 5, "SCALE") == 3.0
    assert feature_distance(None, 5, "SCALE") == 0.0

def test_feature_distance_multi_select():
    assert feature_distance(["a", "b"], ["b", "c"], "MULTI_SELECT") == 1.0 - (1/3)
    assert feature_distance(["a"], ["a"], "MULTI_SELECT") == 0.0

def test_targeted_movement():
    plan = {"interventions": [{"feature_id": "f1", "op": "increase", "target_value": 5}]}
    prof0 = {"f1": 2}
    prof1 = {"f1": 4} # increased, but not 5
    
    res = calculate_targeted_movement([plan], [prof0, prof1])
    assert res["total_targeted"] == 1
    assert res["total_measurable"] == 1
    assert res["achieved_count"] == 1 # increased
    assert res["interventions"][0]["target_achieved"] == "achieved"
