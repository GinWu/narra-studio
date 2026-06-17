from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.cost import CostRecordRead, InvocationLogRead
from backend.app.services.cost_service import CostService, InvocationLogService


router = APIRouter()


@router.get("/experiments/{experiment_id}", response_model=list[CostRecordRead])
def list_experiment_costs(experiment_id: str, db: Session = Depends(get_db)):
    return CostService(db).list_for_experiment(experiment_id)


@router.get("/summary")
def cost_summary(
    provider_id: str | None = None,
    model_id: str | None = None,
    capability_type: str | None = None,
    db: Session = Depends(get_db),
):
    return CostService(db).summarize(
        provider_id=provider_id,
        model_id=model_id,
        capability_type=capability_type,
    )


@router.get("/invocation-logs", response_model=list[InvocationLogRead])
def list_invocation_logs(
    experiment_id: str | None = None,
    task_id: str | None = None,
    provider_id: str | None = None,
    model_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return InvocationLogService(db).list_logs(
        experiment_id=experiment_id,
        task_id=task_id,
        provider_id=provider_id,
        model_id=model_id,
        limit=limit,
    )
