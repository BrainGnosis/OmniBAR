from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class LatteRun(Base):
    __tablename__ = "latte_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    baristas_note: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_breakdown: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    mock_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "temperature": self.temperature,
            "model": self.model,
            "response": self.response,
            "score": self.score,
            "baristas_note": self.baristas_note,
            "scoring_breakdown": self.scoring_breakdown,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "mock_run": self.mock_run,
        }
