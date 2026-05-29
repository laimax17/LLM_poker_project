"""Tests for the LLM provider/model registry and unified client wiring."""
import os

from backend.src.ai.providers import (
    PROVIDERS,
    get_provider,
    models_payload,
    provider_api_key,
    provider_available,
)
from backend.src.ai.openai_client import OpenAICompatibleClient


def test_core_providers_present():
    assert 'openrouter' in PROVIDERS
    assert 'deepseek' in PROVIDERS
    assert 'ollama' in PROVIDERS


def test_provider_base_urls():
    assert PROVIDERS['openrouter'].base_url == 'https://openrouter.ai/api/v1'
    assert PROVIDERS['deepseek'].base_url == 'https://api.deepseek.com/v1'


def test_ollama_needs_no_key():
    assert PROVIDERS['ollama'].requires_key is False
    assert provider_available('ollama') is True


def test_cloud_provider_availability_follows_key(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    assert provider_available('openrouter') is False
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    assert provider_available('openrouter') is True
    assert provider_api_key('openrouter') == 'sk-test'


def test_unknown_provider():
    assert get_provider('nope') is None
    assert provider_available('nope') is False


def test_models_payload_shape():
    payload = models_payload()
    assert 'providers' in payload and 'models' in payload
    # every model references a known provider
    provider_ids = {p['id'] for p in payload['providers']}
    for m in payload['models']:
        assert m['provider'] in provider_ids
        assert m['id'] and m['label']


def test_models_payload_has_no_secrets(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-secret-value')
    payload = models_payload()
    assert 'sk-secret-value' not in str(payload)


def test_client_construction_does_not_require_key():
    # Should construct (with a warning) even without a key; calls would fail later.
    client = OpenAICompatibleClient(
        model='deepseek-chat',
        base_url='https://api.deepseek.com/v1',
        api_key='',
    )
    assert client.model == 'deepseek-chat'
    assert client.base_url == 'https://api.deepseek.com/v1'
