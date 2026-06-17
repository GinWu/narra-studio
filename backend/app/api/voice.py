from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.capabilities import default_adapter_registry
from backend.app.api.deps import get_db
from backend.app.schemas.voice import LabRunRead, TtsRunCreate
from backend.app.services.voice_lab_service import TtsRunInput, VoiceLabService, VoiceLabValidationError
from backend.app.services.voice_profile_service import VoiceProfileError


router = APIRouter()


@router.post("/tts", response_model=LabRunRead)
def run_tts(payload: TtsRunCreate, db: Session = Depends(get_db)):
    try:
        outcome = VoiceLabService(db, default_adapter_registry).run_tts(TtsRunInput(**payload.model_dump()))
    except (VoiceLabValidationError, VoiceProfileError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LabRunRead(
        experiment_id=outcome.experiment.id,
        status=outcome.experiment.status,
        result_mode=outcome.experiment.result_mode,
        output_asset_refs_json=outcome.experiment.output_asset_refs_json,
        error_json=outcome.experiment.error_json,
    )
