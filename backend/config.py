from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from a .env file located beside this module if present
ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()


class Settings(BaseModel):
    """Runtime configuration for the OmniBrew backend."""

    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    mock_mode: bool = Field(
        default_factory=lambda: os.getenv("MOCK_MODE", "true").strip().lower()
        in {"1", "true", "yes"}
    )
    default_model: str = Field(
        default_factory=lambda: os.getenv("LATTE_LAB_MODEL", "gpt-4o-mini")
    )
    scoring_model: str = Field(
        default_factory=lambda: os.getenv("LATTE_LAB_SCORING_MODEL", "gpt-4o-mini")
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("LATTE_LAB_TEMPERATURE", "0.7"))
    )
    database_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "LATTE_LAB_DB",
                str(Path(__file__).resolve().parent / "data" / "latte_lab.db"),
            )
        )
    )
    allow_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("LATTE_LAB_CORS", "http://localhost:5173").split(
                ","
            )
            if origin.strip()
        ]
    )
    

    class Config:
        arbitrary_types_allowed = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
