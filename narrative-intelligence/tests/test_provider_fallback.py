import os
import pytest
from unittest.mock import patch
from core.llm.router import ProviderRouter

@patch.dict(os.environ, {
    "LENS_PRIMARY_PROVIDER": "gemini",
    "LENS_PRIMARY_MODEL": "gemini-test",
    "LENS_FALLBACK_PROVIDER": "groq",
    "LENS_FALLBACK_MODEL": "groq-test",
    "FORGE_PRIMARY_PROVIDER": "groq",
    "FORGE_PRIMARY_MODEL": "groq-test",
    "FORGE_FALLBACK_PROVIDER": "gemini",
    "FORGE_FALLBACK_MODEL": "gemini-test"
})
class TestProviderFallback:
    def test_1_lens_gemini_succeeds(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.return_value = '{"test": "1"}'
                
                router = ProviderRouter("lens")
                res = router.get_structured_output("hi", {})
                
                assert res == '{"test": "1"}'
                assert router.last_metadata["provider"] == "gemini"
                assert router.last_metadata["fallback_used"] is False
                assert mock_gemini.call_count == 1
                assert mock_groq.call_count == 0

    def test_2_lens_gemini_429(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("429 Too Many Requests")
                mock_groq.return_value = '{"test": "2"}'
                
                router = ProviderRouter("lens")
                res = router.get_structured_output("hi", {})
                
                assert res == '{"test": "2"}'
                assert router.last_metadata["provider"] == "groq"
                assert router.last_metadata["fallback_used"] is True
                assert mock_gemini.call_count == 1
                assert mock_groq.call_count == 1

    def test_3_lens_gemini_timeout(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("Timeout")
                mock_groq.return_value = '{"test": "3"}'
                
                router = ProviderRouter("lens")
                res = router.get_structured_output("hi", {})
                
                assert router.last_metadata["provider"] == "groq"
                assert mock_gemini.call_count == 1
                assert mock_groq.call_count == 1

    def test_4_lens_gemini_malformed_json(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("Malformed JSON")
                mock_groq.return_value = '{"test": "4"}'
                
                router = ProviderRouter("lens")
                res = router.get_structured_output("hi", {})
                
                assert router.last_metadata["provider"] == "groq"

    def test_5_forge_groq_succeeds(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_groq.return_value = '{"test": "5"}'
                
                router = ProviderRouter("forge")
                res = router.get_structured_output("hi", {})
                
                assert router.last_metadata["provider"] == "groq"
                assert router.last_metadata["fallback_used"] is False
                assert mock_groq.call_count == 1
                assert mock_gemini.call_count == 0

    def test_6_forge_groq_429(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_groq.side_effect = Exception("429 Too Many Requests")
                mock_gemini.return_value = '{"test": "6"}'
                
                router = ProviderRouter("forge")
                res = router.get_structured_output("hi", {})
                
                assert router.last_metadata["provider"] == "gemini"
                assert router.last_metadata["fallback_used"] is True
                assert mock_groq.call_count == 1
                assert mock_gemini.call_count == 1

    def test_7_forge_groq_timeout(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_groq.side_effect = Exception("Timeout")
                mock_gemini.return_value = '{"test": "7"}'
                
                router = ProviderRouter("forge")
                res = router.get_structured_output("hi", {})
                
                assert router.last_metadata["provider"] == "gemini"
                assert router.last_metadata["fallback_used"] is True

    def test_8_both_providers_fail(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("Error G")
                mock_groq.side_effect = Exception("Error Q")
                
                router = ProviderRouter("lens")
                with pytest.raises(Exception) as excinfo:
                    router.get_structured_output("hi", {})
                    
                assert "Primary (gemini) failed:" in str(excinfo.value)
                assert "Fallback (groq) failed:" in str(excinfo.value)

    def test_9_no_infinite_loop(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("Error G")
                mock_groq.side_effect = Exception("Error Q")
                
                router = ProviderRouter("lens")
                with pytest.raises(Exception):
                    router.get_structured_output("hi", {})
                    
                assert mock_gemini.call_count == 1
                assert mock_groq.call_count == 1

    def test_10_schemas_identical(self):
        with patch('core.llm.gemini_provider.GeminiProvider.get_structured_output') as mock_gemini:
            with patch('core.llm.groq_provider.GroqProvider.get_structured_output') as mock_groq:
                mock_gemini.side_effect = Exception("Fail")
                mock_groq.return_value = '{"test": "val"}'
                
                schema = {"type": "string"}
                
                router = ProviderRouter("lens")
                router.get_structured_output("hi", schema)
                
                # Check args passed to fallback
                args, _ = mock_groq.call_args
                assert args[1] == schema
