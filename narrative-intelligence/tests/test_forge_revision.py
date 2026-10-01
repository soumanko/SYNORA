import json
from unittest.mock import MagicMock
from agents.forge.generator import WritingIntent
from agents.forge.revision_planner import RevisionPlanner
from agents.forge.revision_agent import RevisionAgent
from core.diagnostics.diagnostic_engine import StructuredDiagnostic
from core.taxonomy.schemas import Feature, FeatureType, Dimension

def test_revision_planner():
    tax = {
        "temporal_structure": Feature(
            id="temporal_structure", name="Temporal Structure", dimension=Dimension.PLOT,
            question="Q?", type=FeatureType.SCALE, values=["1", "2", "3"]
        )
    }
    planner = RevisionPlanner(None, taxonomy=tax)
    intent = WritingIntent(
        prompt="Write a story", genre="Sci-Fi", tone="Dark", pov="First person", length=100, constraints=["No aliens"]
    )
    diagnostics = [
        StructuredDiagnostic(
            diagnostic_id="1",
            feature_id="temporal_structure",
            feature_name="Temporal Structure",
            feature_type="scale",
            current_value="1",
            observation="Too linear for this genre",
            rationale="Needs increase",
            actionability="actionable",
            suggested_operation="increase",
            suggested_target_value=None,
            evidence=[],
            priority="high"
        )
    ]
    
    plan = planner.create_revision_plan(diagnostics, intent)
    assert plan["status"] == "revision_planned"
    assert len(plan["interventions"]) == 1
    
    inv = plan["interventions"][0]
    assert inv["target"]["feature_id"] == "temporal_structure"
    assert inv["operation"] == "increase"
    assert "genre: Sci-Fi" in inv["constraints_to_preserve"]
    assert "No aliens" in inv["constraints_to_preserve"]
    assert plan["intent_constraints"]["genre"] == "Sci-Fi"

def test_revision_agent():
    mock_llm = MagicMock()
    
    # Mock structured output
    mock_response = {
        "draft": "This is the revised story with non-linear elements.",
        "word_count": 9,
        "revision_summary": "Added flashbacks."
    }
    mock_llm.get_structured_output.return_value = json.dumps(mock_response)
    
    agent = RevisionAgent(mock_llm)
    intent = WritingIntent("Write a story", "Sci-Fi", "Dark", "First person", 100, [])
    revision_plan = {
        "status": "revision_planned",
        "interventions": [
            {
                "target": {"feature_id": "temporal_structure", "feature_name": "Temporal Structure"},
                "diagnostic_reason": "Too linear",
                "revision_instruction": "Add flashbacks"
            }
        ]
    }
    
    draft_1 = agent.revise_draft(intent, "This is draft 0.", {}, [], revision_plan)
    
    assert draft_1["draft"] == mock_response["draft"]
    assert draft_1["revision_summary"] == mock_response["revision_summary"]
    
    args, kwargs = mock_llm.get_structured_output.call_args
    prompt_used = args[0]
    
    assert "Genre: Sci-Fi" in prompt_used
    assert "Target: Temporal Structure" in prompt_used
    assert "Reason: Too linear" in prompt_used
    assert "This is draft 0." in prompt_used
