from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.capabilities import default_adapter_registry
from backend.app.api.deps import get_db
from backend.app.schemas.audio import AudioRunRead, SttRunCreate, VoiceCloneRunCreate
from backend.app.services.audio_input_validator import AudioInputValidationError
from backend.app.services.audio_lab_service import AudioLabService, SttRunInput, VoiceCloneRunInput
from backend.app.services.voice_profile_service import VoiceProfileError


router = APIRouter()


@router.post("/stt", response_model=AudioRunRead)
def run_stt(payload: SttRunCreate, db: Session = Depends(get_db)):
    try:
        outcome = AudioLabService(db, default_adapter_registry).run_stt(SttRunInput(**payload.model_dump()))
    except AudioInputValidationError as exc:
        raise HTTPException(status_code=400, detail={"error_type": exc.code, "message": exc.message}) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cap = outcome.capability_outcome
    return AudioRunRead(
        experiment_id=cap.experiment.id,
        status=cap.experiment.status,
        result_mode=cap.experiment.result_mode,
        output_text=cap.experiment.output_text,
        output_asset_refs_json=cap.experiment.output_asset_refs_json,
        error_json=cap.experiment.error_json,
    )


@router.post("/voice-clone", response_model=AudioRunRead)
def run_voice_clone(payload: VoiceCloneRunCreate, db: Session = Depends(get_db)):
    try:
        outcome = AudioLabService(db, default_adapter_registry).run_voice_clone(
            VoiceCloneRunInput(**payload.model_dump())
        )
    except AudioInputValidationError as exc:
        raise HTTPException(status_code=400, detail={"error_type": exc.code, "message": exc.message}) from exc
    except VoiceProfileError as exc:
        raise HTTPException(status_code=400, detail={"error_type": exc.code, "message": exc.message}) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cap = outcome.capability_outcome
    return AudioRunRead(
        experiment_id=cap.experiment.id,
        status=cap.experiment.status,
        result_mode=cap.experiment.result_mode,
        output_text=cap.experiment.output_text,
        output_asset_refs_json=cap.experiment.output_asset_refs_json,
        voice_profile_id=outcome.voice_profile.id if outcome.voice_profile else None,
        error_json=cap.experiment.error_json,
    )
