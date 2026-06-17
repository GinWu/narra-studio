from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.experiment import (
    ExperimentPatch,
    ExperimentRead,
    MarkFailedCaseCreate,
    RerunCommandRead,
)
from backend.app.services.experiment_service import ExperimentService


router = APIRouter()


@router.get("", response_model=list[ExperimentRead])
def list_experiments(
    capability_type: str | None = None,
    status: str | None = None,
    result_mode: str | None = None,
    provider_id: str | None = None,
    model_id: str | None = None,
    project_id: str | None = None,
    shot_id: str | None = None,
    is_best: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return ExperimentService(db).list_experiments(
        capability_type=capability_type,
        status=status,
        result_mode=result_mode,
        provider_id=provider_id,
        model_id=model_id,
        project_id=project_id,
        shot_id=shot_id,
        is_best=is_best,
        limit=limit,
        offset=offset,
    )


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    try:
        return ExperimentService(db).get_experiment(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.patch("/{experiment_id}", response_model=ExperimentRead)
def patch_experiment(experiment_id: str, payload: ExperimentPatch, db: Session = Depends(get_db)):
    try:
        return ExperimentService(db).patch_experiment(experiment_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.post("/{experiment_id}/mark-best", response_model=ExperimentRead)
def mark_best(experiment_id: str, db: Session = Depends(get_db)):
    try:
        return ExperimentService(db).mark_best(experiment_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.post("/{experiment_id}/mark-failed-case", response_model=ExperimentRead)
def mark_failed_case(
    experiment_id: str,
    payload: MarkFailedCaseCreate | None = None,
    db: Session = Depends(get_db),
):
    try:
        return ExperimentService(db).mark_failed_case(
            experiment_id,
            failed_reason=payload.failed_reason if payload else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc


@router.post("/{experiment_id}/rerun", response_model=RerunCommandRead)
def build_rerun_command(experiment_id: str, db: Session = Depends(get_db)):
    try:
        return ExperimentService(db).build_rerun_command(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Experiment not found") from exc
