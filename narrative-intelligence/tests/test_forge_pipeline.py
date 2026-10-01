import json
from unittest.mock import MagicMock
from agents.forge.generator import NarrativeForgeGenerator, WritingIntent

def test_initial_generation():
    # Mock LLM provider
    mock_llm = MagicMock()
    mock_llm.model = "gemini/gemini-1.5-pro"
    mock_llm.provider = "gemini"
    
    # Mock structured output
    mock_response = {
        "content": "This is a test narrative about a brave knight.",
        "metadata": {
            "word_count": 9
        }
    }
    mock_llm.get_structured_output.return_value = json.dumps(mock_response)
    
    generator = NarrativeForgeGenerator(mock_llm)
    intent = WritingIntent(
        prompt="Write a story about a brave knight.",
        genre="Fantasy",
        tone="Heroic",
        pov="Third-person limited",
        length=10,
        constraints=["Must include a dragon"]
    )
    
    draft_0 = generator.generate_initial_draft(intent)
    
    assert draft_0["draft_id"] == "draft_0"
    assert "brave knight" in draft_0["content"]
    assert draft_0["metadata"]["model"] == "gemini/gemini-1.5-pro"
    assert draft_0["metadata"]["provider"] == "gemini"
    assert draft_0["metadata"]["word_count"] == 9
    
    # Verify the prompt passed to LLM
    args, kwargs = mock_llm.get_structured_output.call_args
    prompt_used = args[0]
    schema_used = args[1]
    
    assert "Prompt: Write a story about a brave knight." in prompt_used
    assert "Genre: Fantasy" in prompt_used
    assert "Tone: Heroic" in prompt_used
    assert "POV: Third-person limited" in prompt_used
    assert "Target Length: 10 words" in prompt_used
    assert "Constraints: Must include a dragon" in prompt_used
    assert "content" in schema_used["properties"]
