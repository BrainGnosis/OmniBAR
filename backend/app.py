from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List
from uuid import uuid4
import time
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from scripts.export_benchmarks_snapshot import generate_benchmark_snapshot, save_snapshot

load_dotenv(dotenv_path="/Users/ash/Desktop/OmniBAR/backend/.env")

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None

SNAPSHOT_PATH = Path("frontend/public/api/benchmarks.json")
RUN_HISTORY_PATH = Path("backend/data/run_history.json")
RUN_HISTORY_LIMIT = 100
SUITE_LABELS = {
    "output": "Output",
    "coding": "Coding Challenges",
    "math": "Math Reasoning",
    "custom": "Custom",
    "crisis": "Crisis",
    "all": "All",
}
LLM_HEALTH_MODEL = os.getenv('OMNIBAR_LLM_HEALTH_MODEL', 'gpt-4o-mini')


def _openai_client() -> Any:
    if OpenAI is None:
        raise RuntimeError('openai package not installed. Install openai to enable LLM health checks.')
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable not set.')
    return OpenAI(api_key=api_key)

app = FastAPI(title="OmniBAR Control API", version="0.1.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    suite: str = "output"
    save: bool = True
    threshold: float | None = None


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _append_run_history(entry: dict[str, Any]) -> None:
    history: List[dict[str, Any]] = _load_json(RUN_HISTORY_PATH, [])
    history.insert(0, entry)
    if len(history) > RUN_HISTORY_LIMIT:
        history = history[:RUN_HISTORY_LIMIT]
    _write_json(RUN_HISTORY_PATH, history)


async def _load_snapshot() -> dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        raise HTTPException(status_code=404, detail="Snapshot not found. Run POST /benchmarks/run to generate one.")

    def _load() -> dict[str, Any]:
        with SNAPSHOT_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    return await asyncio.to_thread(_load)


@app.post("/benchmarks/run")
async def run_benchmarks(request: RunRequest) -> dict:
    """Execute the requested suite, optionally persisting the snapshot, and return the payload."""

    if request.save:
        payload = await asyncio.to_thread(save_snapshot, None, request.suite)
    else:
        payload = await asyncio.to_thread(generate_benchmark_snapshot, request.suite)

    threshold = None
    if request.threshold is not None and 0 < request.threshold <= 1:
        threshold = request.threshold

    run_entry = {
        "id": str(uuid4()),
        "suite": request.suite,
        "suiteLabel": SUITE_LABELS.get(request.suite, request.suite.title()),
        "requestedAt": datetime.now(UTC).isoformat(),
        "generatedAt": payload.get("generatedAt"),
        "summary": payload.get("summary", {}),
        "benchmarkCount": len(payload.get("benchmarks", [])),
        "failed": payload.get("summary", {}).get("failed", 0),
        "success": payload.get("summary", {}).get("success", 0),
        "status": "success" if payload.get("summary", {}).get("failed", 0) == 0 else "needs_attention",
        "threshold": threshold,
    }

    await asyncio.to_thread(_append_run_history, run_entry)
    return payload


@app.get("/benchmarks/snapshot")
async def read_snapshot() -> dict:
    """Return the most recently exported snapshot from disk."""

    return await _load_snapshot()


@app.get("/benchmarks")
async def list_benchmarks() -> List[dict[str, Any]]:
    """Return the benchmark roster from the latest snapshot."""

    snapshot = await _load_snapshot()
    return snapshot.get("benchmarks", [])


@app.get("/runs")
async def list_runs() -> List[dict[str, Any]]:
    """Return historical suite runs."""

    def _load_runs() -> List[dict[str, Any]]:
        return _load_json(RUN_HISTORY_PATH, [])

    return await asyncio.to_thread(_load_runs)


@app.delete("/runs")
async def clear_runs() -> dict[str, Any]:
    """Delete the stored run history."""

    def _clear() -> None:
        RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        if RUN_HISTORY_PATH.exists():
            RUN_HISTORY_PATH.unlink()

    await asyncio.to_thread(_clear)
    return {"status": "cleared"}


@app.get("/health/llm")
async def llm_health_check() -> dict[str, Any]:
    """Perform a lightweight LLM call to ensure API connectivity."""

    try:
        client = _openai_client()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    prompt = "Reply with the word OK."
    start = time.perf_counter()

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=LLM_HEALTH_MODEL,
            messages=[
                {"role": "system", "content": "You are a health check worker."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4,
            temperature=0,
        )
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"LLM request failed: {error}")

    latency = time.perf_counter() - start
    output = response.choices[0].message.content.strip() if response.choices else ''
    success = output.upper().startswith('OK')

    return {
        "status": "ok" if success else "unexpected_output",
        "latency": latency,
        "model": LLM_HEALTH_MODEL,
        "output": output,
    }


@app.post("/benchmarks/smoke")
async def run_smoke_test() -> dict[str, Any]:
    """Run a one-off LLM health benchmark and log it."""

    try:
        client = _openai_client()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    prompt = "What is 2 + 2? Reply with just the number."
    start = time.perf_counter()

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=LLM_HEALTH_MODEL,
            messages=[
                {"role": "system", "content": "You are a calculator."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4,
            temperature=0,
        )
        latency = time.perf_counter() - start
        output = response.choices[0].message.content.strip() if response.choices else ''
        success = output.strip() == '4'
    except Exception as error:
        latency = time.perf_counter() - start
        output = str(error)
        success = False

    run_entry = {
        "id": str(uuid4()),
        "suite": "smoke",
        "suiteLabel": "LLM Smoke Test",
        "requestedAt": datetime.now(UTC).isoformat(),
        "generatedAt": None,
        "summary": {"latency": latency, "output": output},
        "benchmarkCount": 1,
        "failed": 0 if success else 1,
        "success": 1 if success else 0,
        "status": "success" if success else "needs_attention",
        "threshold": None,
    }

    await asyncio.to_thread(_append_run_history, run_entry)

    if not success:
        raise HTTPException(status_code=502, detail="Smoke test failed. Inspect run history for details.")

    return {"status": "success", "latency": latency, "output": output}
