from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.services.security_service import ProjectExportService


router = APIRouter()


@router.get("/projects/{project_id}/manifest")
def export_project_manifest(project_id: str, include_discarded: bool = False, db: Session = Depends(get_db)):
    try:
        return ProjectExportService(db).build_manifest(project_id, include_discarded=include_discarded)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
