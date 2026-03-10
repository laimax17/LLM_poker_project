"""
OpenRouter LLM client via OpenAI-compatible API.
Uses the openai SDK pointed at OpenRouter's base URL.
Supports any model available on https://openrouter.ai (including free models).
"""
from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI, APIError

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_TIMEOUT = 30.0


class OpenRouterClient(LLMClient):
    """Calls any OpenRouter-supported model via the OpenAI-compatible endpoint."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get(
            'OPENROUTER_MODEL', 'google/gemma-2-9b-it:free',
        )
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if not api_key:
            logger.warning('OPENROUTER_API_KEY is not set; OpenRouter calls will fail')
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout=OPENROUTER_TIMEOUT,
        )
        logger.info('OpenRouterClient initialised: model=%s', self.model)

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': user_prompt},
                ],
            )
            content = completion.choices[0].message.content or ''
            logger.debug('OpenRouterClient response (%d chars)', len(content))
            return content
        except APIError as exc:
            logger.error('OpenRouterClient API error: %s', exc)
            raise
        except Exception as exc:
            logger.error('OpenRouterClient unexpected error: %s', exc)
            raise

    async def health_check(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=1,
            )
            return True
        except Exception as exc:
            logger.warning('OpenRouterClient health check failed: %s', exc)
            return False
