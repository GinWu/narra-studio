from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.evaluation import CompareConclusionCreate, CompareItemsCreate, EvaluationRead, EvaluationUpsert
from backend.app.services.evaluation_service import CompareService, EvaluationService, EvaluationValidationError


router = APIRouter()


@router.get("", response_model=list[EvaluationRead])
def list_evaluations(
    target_type: str | None = None,
    target_id: str | None = None,
    compare_group_id: str | None = None,
    db: Session = Depends(get_db),
):
    return EvaluationService(db).list_evaluations(
        target_type=target_type,
        target_id=target_id,
        compare_group_id=compare_group_id,
    )


@router.post("/upsert", response_model=EvaluationRead)
def upsert_evaluation(payload: EvaluationUpsert, db: Session = Depends(get_db)):
    try:
        return EvaluationService(db).upsert_evaluation(**payload.model_dump())
    except (KeyError, EvaluationValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare/conclusion", response_model=EvaluationRead)
def save_compare_conclusion(payload: CompareConclusionCreate, db: Session = Depends(get_db)):
    return EvaluationService(db).save_compare_conclusion(**payload.model_dump())


@router.post("/compare/items")
def get_compare_items(payload: CompareItemsCreate, db: Session = Depends(get_db)):
    return CompareService(db).get_compare_items(payload.experiment_ids)
