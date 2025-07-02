from __future__ import annotations

from abc import ABC, abstractmethod


class LLMBase(ABC):
    """Base interface for all LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt."""
        raise NotImplementedError
