"""
Qwen (DashScope) LLM client via OpenAI-compatible API.
Uses the openai SDK pointed at Alibaba's DashScope base URL.
"""
import logging
import os

from openai import AsyncOpenAI, APIError

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QWEN_TIMEOUT = 60.0


class QwenClient(LLMClient):
    """Calls Alibaba DashScope Qwen models via the OpenAI-compatible endpoint."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get('QWEN_MODEL', 'qwen-plus')
        api_key = os.environ.get('DASHSCOPE_API_KEY', '')
        if not api_key:
            logger.warning('DASHSCOPE_API_KEY is not set; Qwen calls will fail')
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=DASHSCOPE_BASE_URL,
            timeout=QWEN_TIMEOUT,
        )
        logger.info('QwenClient initialised: model=%s', self.model)

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
            logger.debug('QwenClient response (%d chars)', len(content))
            return content
        except APIError as exc:
            logger.error('QwenClient API error: %s', exc)
            raise
        except Exception as exc:
            logger.error('QwenClient unexpected error: %s', exc)
            raise

    async def health_check(self) -> bool:
        try:
            # Minimal test request to check key validity
            await self._client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=1,
            )
            return True
        except Exception as exc:
            logger.warning('QwenClient health check failed: %s', exc)
            return False
