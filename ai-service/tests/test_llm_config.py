import pytest
from app.core.config import settings
from app.services.llm_client import llm_client, log_llm_config
from app.services.classification.llm_classifier import classify_with_llm


def test_llm_config_standardization():
    """Verifies provider configuration, model selection, and API key detection without exposing secrets."""
    assert settings.active_llm_provider == "groq"
    assert "qwen" in settings.active_llm_model.lower()
    
    # Verify is_llm_configured property returns boolean
    assert isinstance(settings.is_llm_configured, bool)
    
    # Safe diagnostics logging (should not throw and should not leak keys)
    log_llm_config()


def test_llm_client_initialization():
    """Verifies that llm_client initializes properly with standardized settings."""
    assert llm_client is not None
    if settings.is_llm_configured:
        ready = llm_client._ensure_initialized()
        assert ready is True
        assert llm_client._provider == "groq"
        assert "qwen" in llm_client._model.lower()


@pytest.mark.asyncio
async def test_llm_classifier_fallback_on_empty_candidates():
    """Verifies that LLM classifier cleanly falls back when no candidates are provided."""
    res = await classify_with_llm(
        business_text="something random",
        normalized_concept="something random",
        language_code="en",
        ontology_candidates=[],
        nic_candidates=[]
    )
    assert res is None


@pytest.mark.asyncio
async def test_llm_classifier_hallucination_protection():
    """Verifies that if candidates are provided, LLM response is bounded to existing candidate IDs/codes."""
    mock_ontology = [
        {"id": "ont_rice_mill", "sector": "Manufacturing", "category": "Grain", "sub_category": "Rice", "specific_business": "Rice Mill"}
    ]
    mock_nic = [
        {"code": "10612", "title": "Rice milling"}
    ]
    
    # If LLM is available, it should return a valid candidate ID from mock list
    if settings.is_llm_configured:
        res = await classify_with_llm(
            business_text="I want to start a rice mill in Mandya",
            normalized_concept="rice mill",
            language_code="en",
            ontology_candidates=mock_ontology,
            nic_candidates=mock_nic
        )
        if res is not None:
            assert res.get("selected_ontology_id") == "ont_rice_mill"
            assert res.get("selected_nic_code") == "10612"
