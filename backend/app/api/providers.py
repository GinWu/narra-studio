from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.provider import ProviderCreate, ProviderRead, ProviderTestRead, ProviderUpdate
from backend.app.services.provider_service import ProviderService


router = APIRouter()


@router.get("", response_model=list[ProviderRead])
def list_providers(db: Session = Depends(get_db)):
    return ProviderService(db).list_providers()


@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)):
    return ProviderService(db).create_provider(payload.model_dump(exclude_unset=True))


@router.post("/seed-defaults", response_model=list[ProviderRead])
def seed_default_providers(db: Session = Depends(get_db)):
    return ProviderService(db).seed_defaults()


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ProviderService(db).get_provider(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(provider_id: str, payload: ProviderUpdate, db: Session = Depends(get_db)):
    try:
        return ProviderService(db).update_provider(provider_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.delete("/{provider_id}", response_model=ProviderRead)
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ProviderService(db).delete_provider(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc


@router.post("/{provider_id}/test-connection", response_model=ProviderTestRead)
def test_provider_connection(provider_id: str, db: Session = Depends(get_db)):
    try:
        return ProviderService(db).test_connection(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found") from exc
