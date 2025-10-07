from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
