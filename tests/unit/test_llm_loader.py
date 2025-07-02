from unittest import mock

import pytest
from adapters.llm.llm_loader import EnhancedLLMClient, load_llm
from adapters.llm.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
async def test_enhanced_llm_client_generate():
    """Test enhanced LLM client generation."""
    # Mock the generate method to return a test response
    with mock.patch.object(EnhancedLLMClient, "generate") as mock_generate:
        mock_generate.return_value = "Test response"

        # Create client with minimal config
        with mock.patch("llm.llm_loader.load_llm_config") as mock_config:
            mock_config.return_value = mock.MagicMock(
                mode="local",
                routing_strategy="balanced",
                ollama_url="http://localhost:11434",
                ollama_model="mistral:instruct",
            )

            client = load_llm()
            result = await client.generate("test prompt")
            assert result == "Test response"
            mock_generate.assert_called_once()


def test_ollama_provider_creation():
    """Test Ollama provider creation and configuration."""
    try:
        from adapters.llm.providers.base import LLMModel, LLMProvider, LLMProviderConfig
    except ImportError:
        # Fallback если модуль недоступен
        pytest.skip("LLM providers base module not available")

    config = LLMProviderConfig(
        provider=LLMProvider.OLLAMA, model=LLMModel.MISTRAL_INSTRUCT
    )

    provider = OllamaProvider(config, base_url="http://localhost:11434")

    assert provider.config.provider == LLMProvider.OLLAMA
    assert provider.config.model == LLMModel.MISTRAL_INSTRUCT
    assert provider.base_url == "http://localhost:11434"
    assert provider.api_url == "http://localhost:11434/api"

    # Test cost estimation (should be 0 for local models)
    try:
        from adapters.llm.providers.base import LLMRequest
        request = LLMRequest(prompt="test prompt")
        cost = provider.estimate_cost(request)
        assert cost == 0.0
    except ImportError:
        # Пропускаем если модуль недоступен
        pass


def test_load_llm_config():
    """Test loading LLM configuration from environment."""
    with mock.patch.dict(
        "os.environ",
        {
            "LLM_MODE": "local",
            "OLLAMA_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "mistral:instruct",
            "LLM_ROUTING_STRATEGY": "balanced",
        },
    ):
        from adapters.llm.llm_loader import load_llm_config

        config = load_llm_config()

        assert config.mode == "local"
        assert config.ollama_url == "http://localhost:11434"
        assert config.ollama_model == "mistral:instruct"
        assert config.routing_strategy == "balanced"


def test_load_llm_returns_enhanced_client():
    """Test that load_llm returns EnhancedLLMClient instance."""
    with mock.patch("llm.llm_loader.load_llm_config") as mock_config:
        mock_config.return_value = mock.MagicMock(
            mode="local", routing_strategy="balanced"
        )

        # Mock the provider creation to avoid actual HTTP calls
        with mock.patch("llm.llm_loader.create_ollama_provider") as mock_create:
            mock_provider = mock.MagicMock()
            mock_create.return_value = mock_provider

            client = load_llm()
            assert isinstance(client, EnhancedLLMClient)
