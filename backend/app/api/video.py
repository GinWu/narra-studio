from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.capabilities import default_adapter_registry
from backend.app.api.deps import get_db
from backend.app.schemas.video import VideoGenerationCreate, VideoTaskRead
from backend.app.services.video_lab_service import VideoGenerationInput, VideoLabService, VideoLabValidationError


router = APIRouter()


@router.post("/generate", response_model=VideoTaskRead)
def generate_video(payload: VideoGenerationCreate, db: Session = Depends(get_db)):
    try:
        run_immediately = payload.run_immediately
        data = payload.model_dump()
        data.pop("run_immediately", None)
        result = VideoLabService(db, default_adapter_registry).create_video_task(
            VideoGenerationInput(**data),
            run_immediately=run_immediately,
        )
        return VideoTaskRead(task_id=result.task_id, experiment_id=result.experiment_id, status=result.status)
    except VideoLabValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
