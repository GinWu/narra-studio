from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.capabilities import default_adapter_registry
from backend.app.api.deps import get_db
from backend.app.db.models import Shot
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectItemCreate,
    ProjectItemRead,
    ProjectRead,
    ProjectUpdate,
    ScriptVersionCreate,
    ScriptVersionRead,
    ScriptFromTranscriptCreate,
    ShotAssetSelect,
    ShotCreate,
    ShotRead,
    ShotVoiceoverGenerateCreate,
    ShotUpdate,
)
from backend.app.services.project_service import ProjectService
from backend.app.services.voice_lab_service import TtsRunInput, VoiceLabService, VoiceLabValidationError
from backend.app.services.voice_profile_service import VoiceProfileError


router = APIRouter()


@router.get("", response_model=list[ProjectRead])
def list_projects(status: str | None = None, db: Session = Depends(get_db)):
    return ProjectService(db).list_projects(status=status)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return ProjectService(db).create_project(payload.model_dump(exclude_unset=True))


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).get_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).update_project(project_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.delete("/{project_id}", response_model=ProjectRead)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).delete_project(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/{project_id}/items", response_model=ProjectItemRead)
def add_project_item(project_id: str, payload: ProjectItemCreate, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).add_item(project_id=project_id, **payload.model_dump())
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/items", response_model=list[ProjectItemRead])
def list_project_items(project_id: str, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).list_items(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/{project_id}/scripts", response_model=ScriptVersionRead)
def create_script(project_id: str, payload: ScriptVersionCreate, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).create_script_version(project_id=project_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/{project_id}/scripts/from-transcript", response_model=ScriptVersionRead)
def create_script_from_transcript(
    project_id: str,
    payload: ScriptFromTranscriptCreate,
    db: Session = Depends(get_db),
):
    try:
        return ProjectService(db).create_script_from_transcript(project_id=project_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/shots", response_model=ShotRead)
def create_shot(project_id: str, payload: ShotCreate, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).create_shot(project_id=project_id, **payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.patch("/{project_id}/shots/{shot_id}", response_model=ShotRead)
def update_shot(
    project_id: str,
    shot_id: str,
    payload: ShotUpdate,
    db: Session = Depends(get_db),
):
    try:
        # Check project first
        ProjectService(db).get_project(project_id)
        # Verify shot exists and belongs to project
        shot = db.get(Shot, shot_id)
        if shot is None or shot.deleted_at is not None or shot.project_id != project_id:
            raise KeyError("shot_not_found")
        return ProjectService(db).update_shot(shot_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{project_id}/shots/{shot_id}/generate-voiceover", response_model=ShotRead)
def generate_shot_voiceover(
    project_id: str,
    shot_id: str,
    payload: ShotVoiceoverGenerateCreate,
    db: Session = Depends(get_db),
):
    service = ProjectService(db)
    try:
        project = service.get_project(project_id)
        shot = db.get(Shot, shot_id)
        if shot is None or shot.deleted_at is not None or shot.project_id != project_id:
            raise KeyError("shot_not_found")
        voiceover_text = (shot.voiceover_text or (shot.metadata_json or {}).get("voiceover_text") or "").strip()
        if not voiceover_text:
            raise ValueError("voiceover_text is required")
        voice_profile_id = (
            payload.voice_profile_id
            or (shot.metadata_json or {}).get("voice_profile_id")
            or (project.metadata_json or {}).get("default_voice_profile_id")
        )
        voice_config = {"voice_profile_id": voice_profile_id} if voice_profile_id else None
        outcome = VoiceLabService(db, default_adapter_registry).run_tts(
            TtsRunInput(
                text=voiceover_text,
                model_id=payload.model_id,
                voice=payload.voice,
                voice_id=payload.voice_id,
                voice_config=voice_config,
                params_json=payload.params_json,
                commercial_use=payload.commercial_use,
                explicit_confirm=payload.explicit_confirm,
                project_id=project_id,
                shot_id=shot_id,
            )
        )
        refs = outcome.experiment.output_asset_refs_json or []
        audio_ref = next((ref for ref in refs if ref.get("asset_type") == "audio"), None)
        if not audio_ref:
            raise ValueError("voiceover_asset_not_created")
        updated = service.select_shot_asset(shot_id, asset_type="audio", asset_id=audio_ref["asset_id"])
        service.add_item(
            project_id=project_id,
            item_type="asset",
            target_id=audio_ref["asset_id"],
            role="shot_voiceover",
            metadata_json={"shot_id": shot_id, "source_experiment_id": outcome.experiment.id},
        )
        return updated
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, VoiceLabValidationError, VoiceProfileError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/shots/{shot_id}/select-asset", response_model=ShotRead)
def select_shot_asset(shot_id: str, payload: ShotAssetSelect, db: Session = Depends(get_db)):
    try:
        return ProjectService(db).select_shot_asset(shot_id, **payload.model_dump())
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/shots", response_model=list[ShotRead])
def list_project_shots(project_id: str, db: Session = Depends(get_db)):
    from backend.app.db.models import Shot
    from sqlalchemy import select
    return list(db.scalars(select(Shot).where(Shot.deleted_at.is_(None)).where(Shot.project_id == project_id)).all())


@router.get("/{project_id}/scripts", response_model=list[ScriptVersionRead])
def list_project_scripts(project_id: str, db: Session = Depends(get_db)):
    return ProjectService(db).list_script_versions(project_id)
