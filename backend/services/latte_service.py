from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..models import LatteRun
from ..schemas import (
    LatteCreateRequest,
    LatteDailyScore,
    LatteRollupModelStats,
    LatteRollupResponse,
)
from .scoring import evaluate_with_omnibar


def _invoke_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    settings: Settings,
    mock_mode: bool,
) -> tuple[str, dict[str, Any], int]:
    if mock_mode or not settings.openai_api_key:
        response = (
            "☕️ Mock Brew coming right up! Here's a friendly reply based on your prompt: "
            f"{user_prompt.strip()}"
        )
        token_count = len(response.split())
        metadata = {
            "mode": "mock",
            "approx_tokens": token_count,
        }
        return response, metadata, 0

    chat = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openai_api_key,
        max_retries=2,
    )
    start = time.perf_counter()
    ai_message = chat.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    metadata = getattr(ai_message, "response_metadata", {}) or {}
    token_usage = metadata.get("token_usage") or {}
    if not token_usage:
        approx_tokens = len(ai_message.content.split())
        token_usage = {
            "prompt_tokens": None,
            "completion_tokens": approx_tokens,
            "total_tokens": approx_tokens,
        }
    return ai_message.content, token_usage, latency_ms


def create_latte_run(
    db: Session, payload: LatteCreateRequest, settings: Settings | None = None
) -> LatteRun:
    settings = settings or get_settings()
    effective_mock = settings.mock_mode if payload.mock is None else payload.mock
    effective_settings = settings.model_copy(update={"mock_mode": effective_mock})

    response_text, llm_metadata, latency_ms = _invoke_llm(
        system_prompt=payload.system_prompt,
        user_prompt=payload.user_prompt,
        model=payload.model,
        temperature=payload.temperature,
        settings=settings,
        mock_mode=effective_mock,
    )

    score_result = evaluate_with_omnibar(
        response=response_text,
        system_prompt=payload.system_prompt,
        user_prompt=payload.user_prompt,
        settings=effective_settings,
    )

    prompt_tokens = (
        llm_metadata.get("prompt_tokens") if isinstance(llm_metadata, dict) else None
    )
    completion_tokens = (
        llm_metadata.get("completion_tokens")
        if isinstance(llm_metadata, dict)
        else None
    )
    total_tokens = (
        llm_metadata.get("total_tokens") if isinstance(llm_metadata, dict) else None
    )

    run = LatteRun(
        created_at=datetime.now(timezone.utc),
        system_prompt=payload.system_prompt,
        user_prompt=payload.user_prompt,
        temperature=payload.temperature,
        model=payload.model,
        response=response_text,
        score=score_result.score,
        baristas_note=score_result.note,
        scoring_breakdown=score_result.breakdown,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        mock_run=effective_mock,
    )

    db.add(run)
    db.flush()
    db.commit()
    return run


def fetch_runs(db: Session) -> list[LatteRun]:
    return db.query(LatteRun).order_by(LatteRun.created_at.desc()).all()


def get_rollups(db: Session) -> LatteRollupResponse:
    total_runs = db.query(func.count(LatteRun.id)).scalar() or 0
    average_score = db.query(func.avg(LatteRun.score)).scalar() or 0.0
    mock_runs = (
        db.query(func.count(LatteRun.id)).filter(LatteRun.mock_run.is_(True)).scalar()
        or 0
    )

    model_stats: list[LatteRollupModelStats] = []
    for model_name, avg_score, count, last_run in (
        db.query(
            LatteRun.model,
            func.avg(LatteRun.score),
            func.count(LatteRun.id),
            func.max(LatteRun.created_at),
        )
        .group_by(LatteRun.model)
        .order_by(func.avg(LatteRun.score).desc())
    ):
        model_stats.append(
            LatteRollupModelStats(
                model=model_name,
                average_score=float(avg_score or 0.0),
                run_count=int(count or 0),
                last_run=last_run,
            )
        )

    daily_rows: list[LatteDailyScore] = []
    for day, avg_score, count in (
        db.query(
            func.date(LatteRun.created_at),
            func.avg(LatteRun.score),
            func.count(LatteRun.id),
        )
        .group_by(func.date(LatteRun.created_at))
        .order_by(func.date(LatteRun.created_at))
    ):
        daily_rows.append(
            LatteDailyScore(
                date=str(day),
                average_score=float(avg_score or 0.0),
                run_count=int(count or 0),
            )
        )

    success_rate = 0.0
    if total_runs:
        success_count = (
            db.query(func.count(LatteRun.id)).filter(LatteRun.score >= 0.8).scalar()
            or 0
        )
        success_rate = float(success_count) / float(total_runs)

    return LatteRollupResponse(
        total_runs=int(total_runs),
        average_score=float(round(average_score, 3)),
        success_rate=round(success_rate, 3),
        mock_runs=int(mock_runs),
        model_breakdown=model_stats,
        daily_scores=daily_rows,
    )
