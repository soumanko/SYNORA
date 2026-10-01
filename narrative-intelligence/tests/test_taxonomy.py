import pytest
from core.taxonomy.schemas import Feature, FeatureType, Dimension
from core.taxonomy.taxonomy_loader import TaxonomyLoader
import json
import tempfile
from pathlib import Path

@pytest.fixture
def mock_taxonomy_file():
    mock_data = [
        {
            "id": "F001",
            "name": "Protagonist Name",
            "dimension": "Agents",
            "question": "What is the name of the protagonist?",
            "type": "categorical",
            "values": ["Named", "Unnamed"]
        }
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(mock_data, f)
        temp_path = f.name
    
    yield temp_path
    
    Path(temp_path).unlink()

def test_taxonomy_loader(mock_taxonomy_file):
    loader = TaxonomyLoader(taxonomy_path=mock_taxonomy_file)
    features = loader.load_taxonomy()
    
    assert len(features) == 1
    assert "F001" in features
    assert features["F001"].dimension == Dimension.AGENTS
    assert features["F001"].type == FeatureType.CATEGORICAL
