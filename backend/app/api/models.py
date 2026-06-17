from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.model_registry import ModelCreate, ModelRead, ModelUpdate
from backend.app.services.model_registry_service import ModelRegistryService


router = APIRouter()


@router.get("", response_model=list[ModelRead])
def list_models(
    provider_id: str | None = None,
    capability_type: str | None = None,
    enabled: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return ModelRegistryService(db).list_models(
        provider_id=provider_id,
        capability_type=capability_type,
        enabled=enabled,
    )


@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelCreate, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).create_model(payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.post("/seed-bailian", response_model=list[ModelRead])
def seed_bailian_models(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).seed_bailian_models(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.get("/default", response_model=ModelRead)
def get_default_model(capability_type: str, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).get_default_model(capability_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Default model not found") from exc


@router.get("/{model_id}", response_model=ModelRead)
def get_model(model_id: str, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).get_model(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Model not found") from exc


@router.patch("/{model_id}", response_model=ModelRead)
def update_model(model_id: str, payload: ModelUpdate, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).update_model(model_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Model or provider not found") from exc


@router.delete("/{model_id}", response_model=ModelRead)
def delete_model(model_id: str, db: Session = Depends(get_db)):
    try:
        return ModelRegistryService(db).delete_model(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Model not found") from exc
