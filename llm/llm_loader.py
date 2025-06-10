from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from .base import LLMBase


@dataclass
class OllamaLLM(LLMBase):
    base_url: str
    model: str

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.post(
                "/api/generate",
                json={"model": self.model, "prompt": prompt},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")


@dataclass
class OpenAILLM(LLMBase):
    api_key: str
    model: str = "gpt-3.5-turbo"

    async def generate(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


def load_llm() -> LLMBase:
    """Load LLM client according to configuration from environment."""
    mode = os.getenv("MODEL_MODE", "local").lower()
    model_url = os.getenv("MODEL_URL", "http://localhost:11434")
    model_name = os.getenv("MODEL_NAME", "llama3")

    if mode == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        return OpenAILLM(api_key=api_key, model=model_name)

    return OllamaLLM(base_url=model_url, model=model_name)
