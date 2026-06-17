from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.asset import AssetRead, UploadAssetCreate
from backend.app.services.asset_service import AssetService, FileService, StorageRepairService


router = APIRouter()


@router.get("", response_model=list[AssetRead])
def list_assets(
    asset_type: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    source_experiment_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return AssetService(db).list_assets(
        asset_type=asset_type,
        status=status,
        project_id=project_id,
        source_experiment_id=source_experiment_id,
        limit=limit,
        offset=offset,
    )


@router.get("/repair/check")
def check_asset_storage(db: Session = Depends(get_db)):
    return StorageRepairService(AssetService(db)).check_assets()


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    try:
        return AssetService(db).get_asset(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc


@router.get("/{asset_id}/download")
def download_asset(asset_id: str, db: Session = Depends(get_db)):
    service = AssetService(db)
    try:
        asset = service.get_asset(asset_id)
        path = service.get_download_path(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=410, detail="Asset has been deleted") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Asset file missing") from exc
    return FileResponse(path, media_type=asset.mime_type, filename=asset.filename)


@router.post("/upload", response_model=AssetRead)
def upload_asset(payload: UploadAssetCreate, db: Session = Depends(get_db)):
    content = base64.b64decode(payload.content_base64)
    return FileService(AssetService(db)).save_upload_bytes(
        asset_type=payload.asset_type,
        filename=payload.filename,
        content=content,
        mime_type=payload.mime_type,
        project_id=payload.project_id,
    )


@router.post("/{asset_id}/discard", response_model=AssetRead)
def discard_asset(asset_id: str, db: Session = Depends(get_db)):
    try:
        return AssetService(db).discard_asset(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc


@router.post("/{asset_id}/delete", response_model=AssetRead)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    try:
        return AssetService(db).delete_asset(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
