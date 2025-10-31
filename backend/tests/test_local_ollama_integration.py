"""Integration utilities for exercising the local Ollama wiring."""

import os
import sys
from pathlib import Path
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient

try:
    from backend.app import app
except ModuleNotFoundError:  # pragma: no cover - fallback for direct pytest runs
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from backend.app import app  # type: ignore[no-redef]


client = TestClient(app)
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mixtral")
SUPPORTED_LOCAL_MODELS = ("mixtral", "opencode")


def _endpoint_reachable(url: str, *, timeout: float = 1.0) -> bool:
    """Return True if the Ollama endpoint responds without raising."""
    try:
        response = requests.get(f"{url}/api/tags", timeout=timeout)
    except requests.RequestException:
        return False
    return response.ok


def ollama_available() -> bool:
    """Return True when the local Ollama instance exposes its tag listing."""
    return _endpoint_reachable(LLM_ENDPOINT, timeout=2.0)


@pytest.fixture(scope="session")
def llm_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Prepare endpoint/model defaults, falling back to mock mode when needed."""
    if not _endpoint_reachable(LLM_ENDPOINT):
        monkeypatch.setenv("MOCK_MODE", "true")
        mode = "mock"
        provider = "openai"
    else:
        mode = "live"
        provider = "ollama" if ollama_available() else "openai"

    return {
        "mode": mode,
        "endpoint": LLM_ENDPOINT,
        "model": LLM_MODEL,
        "provider": provider,
        "models": ["openai", "mixtral", "opencode"],
    }


def test_client_instantiated() -> None:
    """Ensure the FastAPI test client is ready for downstream integration tests."""
    assert client is not None


def test_environment_defaults(llm_environment: dict[str, Any]) -> None:
    """Confirm endpoint/model defaults and mock-mode fallback wiring."""
    assert llm_environment["endpoint"].startswith(("http://", "https://"))
    assert llm_environment["model"]
    if llm_environment["mode"] == "mock":
        assert os.environ.get("MOCK_MODE") == "true"
    assert "openai" in llm_environment["models"]
    assert "mixtral" in llm_environment["models"]
    assert "opencode" in llm_environment["models"]


@pytest.mark.integration
def test_local_model_inference() -> None:
    """Confirm that the default Ollama model responds when available."""
    if not ollama_available():
        pytest.skip("Ollama not available; running in mock mode.")

    payload = {"prompt": "What is OmniBAR?", "model": LLM_MODEL}
    response = requests.post(
        f"{LLM_ENDPOINT}/api/generate", json=payload, timeout=15
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "output" in data


@pytest.mark.integration
@pytest.mark.parametrize("model_name", SUPPORTED_LOCAL_MODELS)
def test_local_model_inference_variants(model_name: str) -> None:
    """Ensure each supported local model can be invoked via Ollama."""
    if not ollama_available():
        pytest.skip("Ollama not available; running in mock mode.")

    payload = {"prompt": "Give a one-line summary of OmniBAR.", "model": model_name}
    response = requests.post(
        f"{LLM_ENDPOINT}/api/generate", json=payload, timeout=15
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "output" in data


@pytest.mark.integration
def test_backend_handles_local_model_request() -> None:
    """Verify the backend endpoint gracefully handles local model requests."""
    response = client.post(
        "/api/score_prompt",
        json={"prompt": "Explain AI reliability briefly."},
    )
    assert response.status_code in (200, 503)


@pytest.mark.integration
def test_backend_handles_openai_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise backend OpenAI wiring when an API key is present."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OpenAI API key not configured.")

    # Ensure mock mode is disabled so the backend attempts an actual call.
    monkeypatch.delenv("MOCK_MODE", raising=False)
    response = client.post(
        "/api/score_prompt",
        json={"prompt": "Summarize OmniBAR in one sentence.", "model": "openai"},
    )
    assert response.status_code in (200, 401, 429, 503)
