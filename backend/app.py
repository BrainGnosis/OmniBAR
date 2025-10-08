from __future__ import annotations

import sys
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

try:
    from .config import get_settings
    from .database import Base, SessionLocal, engine
    from .models import LatteRun
    from .schemas import (
        ConfigResponse,
        LatteCreateRequest,
        LatteRollupResponse,
        LatteRunDetailResponse,
        LatteRunListResponse,
    )
    from .services.latte_service import create_latte_run, fetch_runs, get_rollups
except ImportError:  # pragma: no cover - direct execution fallback
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from backend.config import get_settings  # type: ignore[no-redef]
    from backend.database import Base, SessionLocal, engine  # type: ignore[no-redef]
    from backend.models import LatteRun  # type: ignore[no-redef]
    from backend.schemas import (  # type: ignore[no-redef]
        ConfigResponse,
        LatteCreateRequest,
        LatteRollupResponse,
        LatteRunDetailResponse,
        LatteRunListResponse,
    )
    from backend.services.latte_service import create_latte_run, fetch_runs, get_rollups  # type: ignore[no-redef]

settings = get_settings()

app = FastAPI(
    title="OmniBrew", version="0.1.0", description="Prompt Trace Scoring with OmniBAR"
)

origins = list(
    dict.fromkeys(
        (settings.allow_origins or [])
        + ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUITE_LABELS = {
    "output": "Calculator Demo Suite",
    "custom": "Custom Agents Suite",
    "crisis": "Crisis Command Suite",
    "all": "Run Everything",
}

SuiteTemplate = dict[str, Any]

SUITE_TEMPLATES: dict[str, list[SuiteTemplate]] = {
    "output": [
        {
            "id": "calc-string-check",
            "name": "Addition String Check",
            "iterations": 5,
            "base_success": 0.93,
            "latency": 0.42,
            "cost": 0.00015,
            "suite": "output",
            "failure_objective": "Addition accurate",
            "failure_reason": "Mismatch between expected string and response.",
        },
        {
            "id": "calc-regex-match",
            "name": "Multiplication Regex",
            "iterations": 4,
            "base_success": 0.88,
            "latency": 0.38,
            "cost": 0.00012,
            "suite": "output",
            "failure_objective": "Regex captures product",
            "failure_reason": "Output failed to match the expected multiplication pattern.",
        },
        {
            "id": "calc-objective-run",
            "name": "Combined Objective Run",
            "iterations": 3,
            "base_success": 0.81,
            "latency": 0.55,
            "cost": 0.0002,
            "suite": "output",
            "failure_objective": "All calculator objectives pass",
            "failure_reason": "One or more scenarios returned incorrect arithmetic.",
        },
    ],
    "custom": [
        {
            "id": "custom-weather",
            "name": "Weather Agent Scenario",
            "iterations": 6,
            "base_success": 0.79,
            "latency": 0.72,
            "cost": 0.00032,
            "suite": "custom",
            "failure_objective": "Weather summary accuracy",
            "failure_reason": "Temperature range omitted or mismatched city.",
        },
        {
            "id": "custom-translate",
            "name": "Translation Agent Accuracy",
            "iterations": 5,
            "base_success": 0.84,
            "latency": 0.63,
            "cost": 0.00029,
            "suite": "custom",
            "failure_objective": "EN→ES translation fidelity",
            "failure_reason": "Idiomatic phrase translated too literally.",
        },
        {
            "id": "custom-fallbacks",
            "name": "Fallback Strategy Guardrails",
            "iterations": 4,
            "base_success": 0.75,
            "latency": 0.81,
            "cost": 0.00033,
            "suite": "custom",
            "failure_objective": "Escalation to human",
            "failure_reason": "Agent failed to surface escalation guidance after tool failure.",
        },
    ],
    "crisis": [
        {
            "id": "crisis-inventory",
            "name": "Inventory Fulfillment",
            "iterations": 7,
            "base_success": 0.77,
            "latency": 0.94,
            "cost": 0.00041,
            "suite": "crisis",
            "failure_objective": "Backorder mitigation",
            "failure_reason": "Critical SKUs not prioritized during shortage.",
        },
        {
            "id": "crisis-routing",
            "name": "Crisis Routing Plan",
            "iterations": 6,
            "base_success": 0.7,
            "latency": 1.02,
            "cost": 0.00037,
            "suite": "crisis",
            "failure_objective": "Delivery routing",
            "failure_reason": "Suboptimal route increased ETA beyond policy.",
        },
        {
            "id": "crisis-communication",
            "name": "Stakeholder Comms",
            "iterations": 5,
            "base_success": 0.83,
            "latency": 0.88,
            "cost": 0.00035,
            "suite": "crisis",
            "failure_objective": "Escalation cadence",
            "failure_reason": "Status updates missed 30-min SLA window.",
        },
    ],
}


def _iter_suite_templates(suite: str) -> Iterable[SuiteTemplate]:
    if suite == "all":
        yield from SUITE_TEMPLATES["output"]
        yield from SUITE_TEMPLATES["custom"]
        yield from SUITE_TEMPLATES["crisis"]
    else:
        yield from SUITE_TEMPLATES.get(suite, [])


def _bounded(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _generate_history_slice(success_rate: float) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    entries: list[dict[str, Any]] = []
    for step in range(3):
        entries.append(
            {
                "timestamp": (now - timedelta(minutes=step * 5))
                .replace(microsecond=0)
                .isoformat(),
                "objective": f"Check {step + 1}",
                "result": success_rate > 0.5 or step < 1,
                "message": "Objective evaluated via OmniBAR mock snapshot.",
            }
        )
    return entries


def _generate_suite_payload(
    suite: str, threshold: float | None = None
) -> dict[str, Any]:
    now = datetime.now(UTC)
    benchmarks: list[dict[str, Any]] = []
    failure_insights: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []

    total_success = 0
    total_failed = 0

    for template in _iter_suite_templates(suite):
        success_rate = _bounded(template["base_success"] + random.uniform(-0.08, 0.08))
        status = "success" if success_rate >= 0.8 else "failed"
        if status == "success":
            total_success += 1
        else:
            total_failed += 1

        latency = max(template["latency"] + random.uniform(-0.2, 0.25), 0.08)
        cost = max(template["cost"] + random.uniform(-0.0002, 0.0002), 0.0)
        tokens = int(600 + random.uniform(-80, 120))

        history = _generate_history_slice(success_rate)
        benchmark = {
            "id": template["id"],
            "name": template["name"],
            "iterations": template["iterations"],
            "successRate": round(success_rate, 3),
            "status": status,
            "updatedAt": now.isoformat(),
            "suite": template.get("suite", suite),
            "latencySeconds": round(latency, 3),
            "tokensUsed": tokens,
            "costUsd": round(cost, 5),
            "confidenceReported": round(_bounded(success_rate * 0.96), 3),
            "confidenceCalibrated": round(_bounded(success_rate * 0.92), 3),
            "history": history,
        }

        if status == "failed":
            benchmark["latestFailure"] = {
                "objective": template.get("failure_objective"),
                "reason": template.get("failure_reason"),
                "category": "quality",
            }
            failure_insights.append(
                {
                    "id": f"insight-{template['id']}",
                    "benchmarkId": template["id"],
                    "benchmarkName": template["name"],
                    "failureRate": round(1 - success_rate, 3),
                    "lastFailureAt": now.isoformat(),
                    "topIssues": [
                        template.get(
                            "failure_reason", "Observed deviation in latest run."
                        ),
                        "Requires operator follow-up.",
                    ],
                    "recommendedFix": "Review prompt strategy and re-run targeted objectives.",
                    "failureCategory": "quality",
                    "history": history,
                }
            )

        benchmarks.append(benchmark)

    total = len(benchmarks)
    summary = {"total": total, "success": total_success, "failed": total_failed}

    recommendations = [
        {
            "id": f"rec-{suite}-playbook",
            "title": "Refresh evaluation playbook",
            "impact": "High",
            "summary": "Review the latest OmniBAR telemetry and confirm coverage of risky objectives.",
            "action": "Draft a remediation checklist for the agent team.",
        },
        {
            "id": f"rec-{suite}-guardrails",
            "title": "Tighten guardrails",
            "impact": "Medium",
            "summary": "Implement guardrail prompts for known failure modes captured in the insights panel.",
            "action": "Experiment with a low-temperature retry policy and compare scores.",
        },
    ]

    live_runs = [
        {
            "id": str(uuid4()),
            "benchmarkName": benchmarks[0]["name"] if benchmarks else "Calculator Demo",
            "status": "completed",
            "currentIteration": benchmarks[0]["iterations"] if benchmarks else 3,
            "totalIterations": benchmarks[0]["iterations"] if benchmarks else 3,
            "startedAt": now.isoformat(),
        },
        {
            "id": str(uuid4()),
            "benchmarkName": "OmniBAR Snapshot Builder",
            "status": "queued",
            "currentIteration": 0,
            "totalIterations": 5,
            "startedAt": None,
        },
    ]

    payload = {
        "benchmarks": benchmarks,
        "summary": summary,
        "liveRuns": live_runs,
        "failureInsights": failure_insights,
        "recommendations": recommendations,
        "generatedAt": now.isoformat(),
        "threshold": threshold,
    }
    return payload


RUN_HISTORY: list[dict[str, Any]] = []
MAX_HISTORY = 30
CURRENT_SNAPSHOT = _generate_suite_payload("output")


def _record_suite_run(
    suite: str, payload: dict[str, Any], threshold: float | None
) -> dict[str, Any]:
    summary = payload["summary"]
    entry = {
        "id": str(uuid4()),
        "suite": suite,
        "suiteLabel": SUITE_LABELS.get(suite, suite.title()),
        "requestedAt": datetime.now(UTC).isoformat(),
        "generatedAt": payload.get("generatedAt"),
        "summary": summary,
        "benchmarkCount": summary["total"],
        "failed": summary["failed"],
        "success": summary["success"],
        "status": "success" if summary["failed"] == 0 else "needs_attention",
        "threshold": threshold,
    }
    RUN_HISTORY.insert(0, entry)
    if len(RUN_HISTORY) > MAX_HISTORY:
        del RUN_HISTORY[MAX_HISTORY:]
    return entry


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"message": "Welcome to OmniBrew"}


@app.get("/config", response_model=ConfigResponse, tags=["meta"])
def read_config() -> ConfigResponse:
    models = {settings.default_model, settings.scoring_model, "gpt-4o-mini", "gpt-4o"}
    return ConfigResponse(
        mock_mode=settings.mock_mode,
        default_model=settings.default_model,
        scoring_model=settings.scoring_model,
        available_models=sorted(models),
    )


@app.post(
    "/lattes", response_model=LatteRunDetailResponse, tags=["lattes"], status_code=201
)
def create_latte(
    payload: LatteCreateRequest, db: Session = Depends(get_db)
) -> LatteRun:
    if not payload.system_prompt.strip():
        raise HTTPException(status_code=400, detail="System prompt is required")
    if not payload.user_prompt.strip():
        raise HTTPException(status_code=400, detail="User prompt is required")

    run = create_latte_run(db, payload, settings=settings)
    db.refresh(run)
    return run


@app.get("/lattes", response_model=LatteRunListResponse, tags=["lattes"])
def list_lattes(db: Session = Depends(get_db)) -> LatteRunListResponse:
    runs = fetch_runs(db)
    return LatteRunListResponse(runs=runs)


@app.get("/lattes/{run_id}", response_model=LatteRunDetailResponse, tags=["lattes"])
def get_latte(run_id: int, db: Session = Depends(get_db)) -> LatteRun:
    run = db.query(LatteRun).filter(LatteRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Latte run not found")
    return run


@app.get("/analytics/rollups", response_model=LatteRollupResponse, tags=["analytics"])
def analytics_rollups(db: Session = Depends(get_db)) -> LatteRollupResponse:
    return get_rollups(db)


class BenchmarkRunRequest(BaseModel):
    suite: str = "output"
    save: bool | None = True
    threshold: float | None = None


@app.get("/benchmarks", tags=["benchmarks"])
def get_benchmarks_snapshot() -> list[dict[str, Any]]:
    global CURRENT_SNAPSHOT
    if not CURRENT_SNAPSHOT["benchmarks"]:
        CURRENT_SNAPSHOT = _generate_suite_payload("output")
    return CURRENT_SNAPSHOT["benchmarks"]


@app.post("/benchmarks/run", tags=["benchmarks"])
def run_benchmark_suite(request: BenchmarkRunRequest) -> dict[str, Any]:
    global CURRENT_SNAPSHOT
    suite = request.suite or "output"
    payload = _generate_suite_payload(suite, request.threshold)
    CURRENT_SNAPSHOT = payload
    _record_suite_run(suite, payload, request.threshold)
    return payload


@app.post("/benchmarks/smoke", tags=["benchmarks"])
def run_smoke_test() -> dict[str, Any]:
    latency = round(random.uniform(0.25, 1.2), 3)
    output = "LLM mock smoke test passed."
    entry = {
        "id": str(uuid4()),
        "suite": "smoke",
        "suiteLabel": "LLM Smoke Test",
        "requestedAt": datetime.now(UTC).isoformat(),
        "generatedAt": datetime.now(UTC).isoformat(),
        "summary": {"total": 1, "success": 1, "failed": 0},
        "benchmarkCount": 1,
        "failed": 0,
        "success": 1,
        "status": "success",
        "threshold": None,
    }
    RUN_HISTORY.insert(0, entry)
    if len(RUN_HISTORY) > MAX_HISTORY:
        del RUN_HISTORY[MAX_HISTORY:]
    return {"status": "ok", "latency": latency, "output": output}


@app.get("/health/llm", tags=["benchmarks"])
def llm_health() -> dict[str, Any]:
    latency = round(random.uniform(0.35, 1.5), 3)
    return {
        "status": "ok",
        "latency": latency,
        "model": settings.default_model,
        "output": "Mock LLM health ping succeeded.",
    }


@app.get("/runs", tags=["benchmarks"])
def get_run_history() -> list[dict[str, Any]]:
    return RUN_HISTORY


@app.delete("/runs", tags=["benchmarks"])
def clear_run_history() -> dict[str, str]:
    RUN_HISTORY.clear()
    return {"message": "Run history cleared"}
