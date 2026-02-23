"""
Abstract interface for LLM provider clients.
Both OllamaClient and QwenClient implement this interface.
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Unified async LLM calling interface."""

    @abstractmethod
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request.
        Returns the model's response as a plain string.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the LLM service is reachable and responding."""
        ...
