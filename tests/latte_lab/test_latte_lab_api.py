from __future__ import annotations

import importlib
from typing import Generator

import pytest
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture()
def latte_lab_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "latte_lab.db"
    monkeypatch.setenv("LATTE_LAB_DB", str(db_path))
    monkeypatch.setenv("MOCK_MODE", "true")

    # Reset cached settings so the new environment variables are applied.
    from backend import config as backend_config

    backend_config.get_settings.cache_clear()

    # Reload database/app modules so they pick up the new settings.
    database_module = importlib.import_module("backend.database")
    importlib.reload(database_module)

    app_module = importlib.import_module("backend.app")
    importlib.reload(app_module)

    # Ensure tables exist for the test database.
    database_module.Base.metadata.create_all(bind=app_module.engine)

    client = TestClient(app_module.app)
    try:
        yield client
    finally:
        client.close()
        backend_config.get_settings.cache_clear()
        # Cleanup to avoid leaking env vars into other tests.
        monkeypatch.delenv("LATTE_LAB_DB", raising=False)
        monkeypatch.delenv("MOCK_MODE", raising=False)


def test_config_endpoint_exposes_expected_defaults(latte_lab_client: TestClient) -> None:
    response = latte_lab_client.get("/config")
    assert response.status_code == 200
    payload = response.json()

    assert payload["default_model"] == "gpt-4o-mini"
    assert payload["scoring_model"] == "gpt-4o-mini"
    assert payload["mock_mode"] is True
    assert sorted(payload["available_models"]) == payload["available_models"]
    assert {"gpt-4o", "gpt-4o-mini"}.issubset(payload["available_models"])


def test_full_latte_flow_in_mock_mode(latte_lab_client: TestClient) -> None:
    create_payload = {
        "system_prompt": "You are an upbeat assistant.",
        "user_prompt": "Share a latte art tip for beginners.",
        "temperature": 0.3,
        "model": "gpt-4o-mini",
        "mock": True,
    }

    create_response = latte_lab_client.post("/lattes", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()

    assert created["mock_run"] is True
    assert 0.0 <= created["score"] <= 1.0
    assert "Mock scoring" in created["baristas_note"]
    assert created["system_prompt"] == create_payload["system_prompt"]
    assert created["user_prompt"] == create_payload["user_prompt"]

    history_response = latte_lab_client.get("/lattes")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history["runs"]) == 1
    assert history["runs"][0]["id"] == created["id"]

    rollups_response = latte_lab_client.get("/analytics/rollups")
    assert rollups_response.status_code == 200
    rollups = rollups_response.json()

    assert rollups["total_runs"] == 1
    assert rollups["mock_runs"] == 1
    assert rollups["average_score"] == pytest.approx(created["score"], rel=1e-6)
    assert rollups["daily_scores"][0]["run_count"] == 1
