import os
import pytest
from src.config import (
    get_openrouter_api_key,
    get_openrouter_model,)

def test_get_openrouter_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the configured OpenRouter API key."""

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    assert get_openrouter_api_key() == "test-key"


def test_get_openrouter_api_key_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error when the OpenRouter API key is missing."""

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    os.environ.pop("OPENROUTER_API_KEY", None)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        get_openrouter_api_key()

def test_get_openrouter_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the configured OpenRouter model identifier."""

    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")

    assert get_openrouter_model() == "openrouter/free"


def test_get_openrouter_model_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error when the OpenRouter model is missing."""

    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    os.environ.pop("OPENROUTER_MODEL", None)

    with pytest.raises(RuntimeError, match="OPENROUTER_MODEL"):
        get_openrouter_model()
        
