from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.db.models import Experiment
from backend.app.schemas.experiment import ExperimentRead
from backend.app.schemas.project import ProjectRead
from backend.app.schemas.voice_profile import (
    SetProjectDefaultVoiceProfile,
    VoiceProfileRead,
    VoiceProfileUpdate,
)
from backend.app.services.voice_profile_service import VoiceProfileError, VoiceProfileService


router = APIRouter()


@router.get("", response_model=list[VoiceProfileRead])
def list_voice_profiles(
    provider_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return VoiceProfileService(db).list_voice_profiles(provider_id=provider_id, status=status)


@router.get("/{voice_profile_id}", response_model=VoiceProfileRead)
def get_voice_profile(voice_profile_id: str, db: Session = Depends(get_db)):
    try:
        return VoiceProfileService(db).get_voice_profile(voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc


@router.patch("/{voice_profile_id}", response_model=VoiceProfileRead)
def update_voice_profile(
    voice_profile_id: str,
    payload: VoiceProfileUpdate,
    db: Session = Depends(get_db),
):
    try:
        return VoiceProfileService(db).update_voice_profile(
            voice_profile_id,
            payload.model_dump(exclude_unset=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc
    except VoiceProfileError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.post("/{voice_profile_id}/disable", response_model=VoiceProfileRead)
def disable_voice_profile(voice_profile_id: str, db: Session = Depends(get_db)):
    try:
        return VoiceProfileService(db).disable_voice_profile(voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc


@router.post("/{voice_profile_id}/mark-revoked", response_model=VoiceProfileRead)
def mark_voice_profile_revoked(voice_profile_id: str, db: Session = Depends(get_db)):
    try:
        return VoiceProfileService(db).mark_revoked(voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc


@router.post("/{voice_profile_id}/mark-expired", response_model=VoiceProfileRead)
def mark_voice_profile_expired(voice_profile_id: str, db: Session = Depends(get_db)):
    try:
        return VoiceProfileService(db).mark_expired(voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc


@router.post("/{voice_profile_id}/set-project-default", response_model=ProjectRead)
def set_project_default_voice_profile(
    voice_profile_id: str,
    payload: SetProjectDefaultVoiceProfile,
    db: Session = Depends(get_db),
):
    try:
        return VoiceProfileService(db).set_project_default_voice_profile(payload.project_id, voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VoiceProfileError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("/{voice_profile_id}/experiments", response_model=list[ExperimentRead])
def list_voice_profile_experiments(voice_profile_id: str, db: Session = Depends(get_db)):
    try:
        VoiceProfileService(db).get_voice_profile(voice_profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="VoiceProfile not found") from exc
    stmt = select(Experiment).where(Experiment.deleted_at.is_(None)).order_by(Experiment.created_at.desc())
    return [
        experiment
        for experiment in db.scalars(stmt).all()
        if (experiment.metadata_json or {}).get("voice_profile_id") == voice_profile_id
    ]
