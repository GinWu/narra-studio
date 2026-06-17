from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.task import TaskCreate, TaskRead
from backend.app.services.task_service import TaskService


router = APIRouter()


@router.get("", response_model=list[TaskRead])
def list_tasks(status: str | None = None, experiment_id: str | None = None, db: Session = Depends(get_db)):
    return TaskService(db).list_tasks(status=status, experiment_id=experiment_id)


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    try:
        return TaskService(db).create_task(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return TaskService(db).get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.post("/{task_id}/cancel", response_model=TaskRead)
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return TaskService(db).request_cancel(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
