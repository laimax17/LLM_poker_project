"""
Ollama LLM client (local inference).
Uses the Ollama REST API with OpenAI-compatible messages format.
"""
import logging
import os

import httpx

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

OLLAMA_TIMEOUT = 30.0
HEALTH_TIMEOUT = 5.0


class OllamaClient(LLMClient):
    """Calls a locally-running Ollama instance via its REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        ).rstrip('/')
        self.model = model or os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')
        logger.info('OllamaClient initialised: url=%s model=%s', self.base_url, self.model)

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        url = f'{self.base_url}/api/chat'
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            'stream': False,
        }
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content: str = data['message']['content']
                logger.debug('OllamaClient response (%d chars)', len(content))
                return content
            except httpx.HTTPError as exc:
                logger.error('OllamaClient HTTP error: %s', exc)
                raise
            except Exception as exc:
                logger.error('OllamaClient unexpected error: %s', exc)
                raise

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
                resp = await client.get(f'{self.base_url}/api/tags')
                return resp.status_code == 200
        except Exception as exc:
            logger.warning('OllamaClient health check failed: %s', exc)
            return False
