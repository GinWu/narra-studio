from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.capabilities import default_adapter_registry
from backend.app.api.deps import get_db
from backend.app.schemas.image import ImageGenerationCreate
from backend.app.schemas.voice import LabRunRead
from backend.app.services.image_lab_service import ImageGenerationInput, ImageLabService, ImageLabValidationError


router = APIRouter()


@router.post("/generate", response_model=LabRunRead)
def generate_image(payload: ImageGenerationCreate, db: Session = Depends(get_db)):
    try:
        outcome = ImageLabService(db, default_adapter_registry).run_image_generation(
            ImageGenerationInput(**payload.model_dump())
        )
    except ImageLabValidationError as exc:
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
