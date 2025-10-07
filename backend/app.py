from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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

settings = get_settings()

app = FastAPI(title="Latte Lab", version="0.1.0", description="Prompt Trace Scoring with OmniBAR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"message": "Welcome to Latte Lab"}


@app.get("/config", response_model=ConfigResponse, tags=["meta"])
def read_config() -> ConfigResponse:
    models = {settings.default_model, settings.scoring_model, "gpt-4o-mini", "gpt-4o"}
    return ConfigResponse(
        mock_mode=settings.mock_mode,
        default_model=settings.default_model,
        scoring_model=settings.scoring_model,
        available_models=sorted(models),
    )


@app.post("/lattes", response_model=LatteRunDetailResponse, tags=["lattes"], status_code=201)
def create_latte(payload: LatteCreateRequest, db: Session = Depends(get_db)) -> LatteRun:
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
