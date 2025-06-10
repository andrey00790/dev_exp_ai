from __future__ import annotations

import os
from dataclasses import dataclass

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


def load_llm() -> LLMBase:
    """Load LLM client according to configuration from environment."""
    mode = os.getenv("MODEL_MODE", "local").lower()
    model_url = os.getenv("MODEL_URL", "http://localhost:11434")
    model_name = os.getenv("MODEL_NAME", "mistral")

    if mode != "local":
        raise ValueError(f"Unsupported MODEL_MODE: {mode}")

    return OllamaLLM(base_url=model_url, model=model_name)
