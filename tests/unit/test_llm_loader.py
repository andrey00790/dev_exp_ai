from unittest import mock

import pytest

from llm.llm_loader import load_llm, OllamaLLM


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


def test_load_llm_bad_mode() -> None:
    with mock.patch.dict('os.environ', {'MODEL_MODE': 'something'}):
        with pytest.raises(ValueError):
            load_llm()
