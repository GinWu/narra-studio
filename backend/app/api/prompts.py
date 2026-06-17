from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.prompt_template import (
    PromptAssembleCreate,
    PromptAssembleRead,
    PromptTemplateCreate,
    PromptTemplateRead,
    PromptTemplateUpdate,
)
from backend.app.services.prompt_template_service import PromptTemplateService


router = APIRouter()


@router.get("", response_model=list[PromptTemplateRead])
def list_templates(
    capability_type: str | None = None,
    version_group_id: str | None = None,
    is_latest: bool | None = Query(default=None),
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return PromptTemplateService(db).list_templates(
        capability_type=capability_type,
        version_group_id=version_group_id,
        is_latest=is_latest,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=PromptTemplateRead, status_code=201)
def create_template(payload: PromptTemplateCreate, db: Session = Depends(get_db)):
    return PromptTemplateService(db).create_template(payload.model_dump(exclude_unset=True))


@router.get("/{template_id}", response_model=PromptTemplateRead)
def get_template(template_id: str, db: Session = Depends(get_db)):
    try:
        return PromptTemplateService(db).get_template(template_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="PromptTemplate not found") from exc


@router.patch("/{template_id}", response_model=PromptTemplateRead)
def update_template(template_id: str, payload: PromptTemplateUpdate, db: Session = Depends(get_db)):
    try:
        return PromptTemplateService(db).update_template(template_id, payload.model_dump(exclude_unset=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="PromptTemplate not found") from exc


@router.delete("/{template_id}", response_model=PromptTemplateRead)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    try:
        return PromptTemplateService(db).delete_template(template_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="PromptTemplate not found") from exc


@router.post("/{template_id}/assemble", response_model=PromptAssembleRead)
def assemble_template(template_id: str, payload: PromptAssembleCreate, db: Session = Depends(get_db)):
    try:
        prompt = PromptTemplateService(db).assemble(template_id, payload.variables)
        return PromptAssembleRead(prompt=prompt)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
