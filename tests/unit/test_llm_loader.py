from unittest import mock

import pytest

from llm.llm_loader import load_llm, OllamaLLM, OpenAILLM


@pytest.mark.asyncio
async def test_ollama_generate() -> None:
    response = mock.MagicMock()
    response.json.return_value = {"response": "hi"}
    response.raise_for_status.return_value = None

    client = mock.AsyncMock()
    client.post = mock.AsyncMock(return_value=response)
    client.__aenter__.return_value = client

    with mock.patch("llm.llm_loader.httpx.AsyncClient", return_value=client):
        llm = OllamaLLM(base_url="http://ollama", model="llama3")
        result = await llm.generate("hello")
        assert result == "hi"


@pytest.mark.asyncio
async def test_openai_generate() -> None:
    response = mock.MagicMock()
    response.json.return_value = {
        "choices": [{"message": {"content": "answer"}}]
    }
    response.raise_for_status.return_value = None

    client = mock.AsyncMock()
    client.post = mock.AsyncMock(return_value=response)
    client.__aenter__.return_value = client

    with mock.patch("llm.llm_loader.httpx.AsyncClient", return_value=client):
        llm = OpenAILLM(api_key="k", model="gpt-test")
        result = await llm.generate("ping")
        assert result == "answer"


def test_load_llm_local() -> None:
    with mock.patch.dict('os.environ', {
        'MODEL_MODE': 'local',
        'MODEL_URL': 'http://ollama',
        'MODEL_NAME': 'llama3',
    }):
        llm = load_llm()
        assert isinstance(llm, OllamaLLM)
        assert llm.base_url == 'http://ollama'
        assert llm.model == 'llama3'


def test_load_llm_openai() -> None:
    with mock.patch.dict('os.environ', {
        'MODEL_MODE': 'openai',
        'OPENAI_API_KEY': 'secret',
        'OPENAI_MODEL': 'gpt-test',
    }):
        llm = load_llm()
        assert isinstance(llm, OpenAILLM)
        assert llm.api_key == 'secret'
        assert llm.model == 'gpt-test'
