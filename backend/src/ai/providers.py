"""
Provider + model registry for the unified LLM backend.

Design goal: "one key per provider, switch models freely".

Every supported cloud provider exposes an OpenAI-compatible API, so they all
share a single client (OpenAICompatibleClient). A provider only needs:
  - a base_url
  - an API-key environment variable (one key)
The model is just a string passed at call time.

Add a provider = add one ProviderSpec; add a model = add one ModelSpec.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    base_url: str
    api_key_env: str
    requires_key: bool = True
    default_model: str = ''


@dataclass(frozen=True)
class ModelSpec:
    id: str        # exact string sent to the API
    label: str     # friendly name shown in the UI
    provider: str  # ProviderSpec.id


# ─── Providers ─────────────────────────────────────────────────────────────────
# Each cloud provider needs exactly ONE key (its api_key_env). Fill whichever
# keys you have in backend/.env — providers without a key show as offline.

PROVIDERS: dict[str, ProviderSpec] = {
    'openrouter': ProviderSpec(
        id='openrouter',
        label='OpenRouter',
        base_url='https://openrouter.ai/api/v1',
        api_key_env='OPENROUTER_API_KEY',
        default_model='openai/gpt-4o-mini',
    ),
    'deepseek': ProviderSpec(
        id='deepseek',
        label='DeepSeek',
        base_url='https://api.deepseek.com/v1',
        api_key_env='DEEPSEEK_API_KEY',
        default_model='deepseek-chat',
    ),
    'ollama': ProviderSpec(
        id='ollama',
        label='Ollama (local)',
        base_url=os.environ.get('OLLAMA_HOST', 'http://localhost:11434'),
        api_key_env='',
        requires_key=False,
        default_model=os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b'),
    ),
}


# ─── Curated model list ─────────────────────────────────────────────────────────
# Shown in the LLMConfigBar dropdown, grouped by provider.

MODELS: list[ModelSpec] = [
    # OpenRouter — one key, many vendors
    ModelSpec('openai/gpt-4o-mini', 'GPT-4o mini', 'openrouter'),
    ModelSpec('openai/gpt-4o', 'GPT-4o', 'openrouter'),
    ModelSpec('anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet', 'openrouter'),
    ModelSpec('google/gemini-2.0-flash-001', 'Gemini 2.0 Flash', 'openrouter'),
    ModelSpec('deepseek/deepseek-chat', 'DeepSeek V3', 'openrouter'),
    ModelSpec('meta-llama/llama-3.3-70b-instruct', 'Llama 3.3 70B', 'openrouter'),
    ModelSpec('qwen/qwen-2.5-72b-instruct', 'Qwen2.5 72B', 'openrouter'),
    # DeepSeek direct — cheapest
    ModelSpec('deepseek-chat', 'DeepSeek Chat', 'deepseek'),
    ModelSpec('deepseek-reasoner', 'DeepSeek Reasoner', 'deepseek'),
    # Ollama local
    ModelSpec('qwen2.5:7b', 'Qwen2.5 7B (local)', 'ollama'),
    ModelSpec('qwen2.5:14b', 'Qwen2.5 14B (local)', 'ollama'),
    ModelSpec('llama3.1:8b', 'Llama 3.1 8B (local)', 'ollama'),
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_provider(provider_id: str) -> Optional[ProviderSpec]:
    return PROVIDERS.get(provider_id)


def provider_api_key(provider_id: str) -> str:
    spec = PROVIDERS.get(provider_id)
    if spec is None or not spec.api_key_env:
        return ''
    return os.environ.get(spec.api_key_env, '')


def provider_available(provider_id: str) -> bool:
    """A provider is usable if it needs no key, or its key is set."""
    spec = PROVIDERS.get(provider_id)
    if spec is None:
        return False
    if not spec.requires_key:
        return True
    return bool(provider_api_key(provider_id))


def models_payload() -> dict[str, Any]:
    """Return the registry for the frontend dropdown (no secrets)."""
    return {
        'providers': [
            {
                'id': p.id,
                'label': p.label,
                'available': provider_available(p.id),
                'defaultModel': p.default_model,
            }
            for p in PROVIDERS.values()
        ],
        'models': [
            {'id': m.id, 'label': m.label, 'provider': m.provider}
            for m in MODELS
        ],
    }
