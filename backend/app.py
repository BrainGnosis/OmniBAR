from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scripts.export_benchmarks_snapshot import generate_benchmark_snapshot, save_snapshot

SNAPSHOT_PATH = Path("frontend/public/api/benchmarks.json")
RUN_HISTORY_PATH = Path("backend/data/run_history.json")
RUN_HISTORY_LIMIT = 100
SUITE_LABELS = {
    "output": "Output",
    "custom": "Custom",
    "crisis": "Crisis",
    "all": "All",
}

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
