from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Benchmark Schemas
class Benchmark(BaseModel):
    id: str = Field(..., example="calc-string-check")
    name: str = Field(..., example="Addition String Check")
    iterations: int = Field(..., example=5)
    successRate: float = Field(..., example=0.93)
    status: str = Field(..., example="success")
    updatedAt: str = Field(..., example="2025-10-07T13:45:00Z")
    suite: str = Field(..., example="output")
    latencySeconds: float = Field(..., example=0.42)
    tokensUsed: int = Field(..., example=621)
    costUsd: float = Field(..., example=0.00015)
    confidenceReported: float = Field(..., example=0.89)
    confidenceCalibrated: float = Field(..., example=0.87)
    history: List[HistoryEntry] = Field(
        ...,
        example=[
            {
                "timestamp": "2025-10-07T13:40:00Z",
                "objective": "Check 1",
                "result": True,
                "message": "Objective evaluated",
            }
        ],
    )
    latestFailure: Optional[Dict[str, Any]] = Field(
        None,
        example={
            "objective": "Addition accurate",
            "reason": "Mismatch between expected string and response.",
            "category": "quality",
        },
    )


class HistoryEntry(BaseModel):
    timestamp: str
    objective: str
    result: bool
    message: str


class Benchmark(BaseModel):
    id: str
    name: str
    iterations: int
    successRate: float
    status: str
    updatedAt: str
    suite: str
    latencySeconds: float
    tokensUsed: int
    costUsd: float
    confidenceReported: float
    confidenceCalibrated: float
    history: List[HistoryEntry]
    latestFailure: Optional[Dict[str, Any]] = None


class BenchmarkSuitePayload(BaseModel):
    benchmarks: List[Benchmark]
    summary: Dict[str, int]
    liveRuns: List[Dict[str, Any]]
    failureInsights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    generatedAt: str
    threshold: Optional[float] = None


# for Latte
class LatteCreateRequest(BaseModel):
    system_prompt: str = Field(..., description="System prompt used for the run")
    user_prompt: str = Field(..., description="User prompt sent to the assistant")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    model: str = Field(..., description="Model identifier to invoke")
    mock: bool | None = Field(None, description="Optional override for mock mode")


class LatteRunBase(BaseModel):
    id: int
    created_at: datetime
    system_prompt: str
    user_prompt: str
    temperature: float
    model: str
    response: str
    score: float
    baristas_note: str
    scoring_breakdown: dict[str, Any]
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    mock_run: bool

    class Config:
        from_attributes = True


class LatteRunListResponse(BaseModel):
    runs: list[LatteRunBase]


class LatteRunDetailResponse(LatteRunBase):
    pass


class LatteRollupModelStats(BaseModel):
    model: str
    average_score: float
    run_count: int
    last_run: datetime | None


class LatteDailyScore(BaseModel):
    date: str
    average_score: float
    run_count: int


class LatteRollupResponse(BaseModel):
    total_runs: int
    average_score: float
    success_rate: float
    mock_runs: int
    model_breakdown: list[LatteRollupModelStats]
    daily_scores: list[LatteDailyScore]


class ConfigResponse(BaseModel):
    mock_mode: bool
    default_model: str
    scoring_model: str
    available_models: list[str]
