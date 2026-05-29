"""
Unified OpenAI-compatible LLM client.

Works with any provider that speaks the OpenAI chat-completions API
(OpenRouter, DeepSeek, OpenAI, DashScope, ...). The provider is selected
purely via base_url + api_key; the model is a runtime string.

This replaces the provider-specific QwenClient — switching provider is now
"change base_url", switching model is "change the model string".
"""
from __future__ import annotations

import logging
from typing import Optional

from openai import APIError, AsyncOpenAI

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0


class OpenAICompatibleClient(LLMClient):
    """Calls any OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = '',
        timeout: float = DEFAULT_TIMEOUT,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.model = model
        self.base_url = base_url
        if not api_key:
            logger.warning(
                'OpenAICompatibleClient created without an API key '
                '(base_url=%s); calls will fail until a key is configured.',
                base_url,
            )
        self._extra_headers = extra_headers
        self._client = AsyncOpenAI(
            api_key=api_key or 'EMPTY',
            base_url=base_url,
            timeout=timeout,
        )
        logger.info(
            'OpenAICompatibleClient initialised: model=%s base_url=%s', model, base_url
        )

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                extra_headers=self._extra_headers,
            )
            content = completion.choices[0].message.content or ''
            logger.debug('LLM response (%d chars) from %s', len(content), self.model)
            return content
        except APIError as exc:
            logger.error('LLM API error (%s): %s', self.model, exc)
            raise
        except Exception as exc:
            logger.error('LLM unexpected error (%s): %s', self.model, exc)
            raise

    async def health_check(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=1,
                extra_headers=self._extra_headers,
            )
            return True
        except Exception as exc:
            logger.warning('LLM health check failed (%s): %s', self.model, exc)
            return False
