"""Async task status as the execution source of truth."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.enums import TASK_STATUSES
from backend.app.db.models import Experiment, Task
from backend.app.services.security_service import SanitizerService
from backend.app.utils.ids import new_id


TASK_TO_EXPERIMENT_STATUS = {
    "pending": "pending",
    "queued": "pending",
    "running": "running",
    "succeeded": "success",
    "failed": "failed",
    "timeout": "timeout",
    "cancelled": "cancelled",
}


class TaskService:
    def __init__(self, session: Session, sanitizer: SanitizerService | None = None) -> None:
        self.session = session
        self.sanitizer = sanitizer or SanitizerService()

    def create_task(
        self,
        *,
        task_type: str,
        experiment_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        request_json: dict[str, Any] | None = None,
        queue_name: str = "default",
        priority: int = 0,
        timeout_seconds: int | None = None,
        max_retries: int = 0,
    ) -> Task:
        if experiment_id:
            experiment = self._get_experiment(experiment_id)
            experiment.result_mode = "async_task"
            experiment.status = "pending"
        task = Task(
            id=new_id("task"),
            task_type=task_type,
            status="pending",
            experiment_id=experiment_id,
            provider_id=provider_id,
            model_id=model_id,
            request_json=self.sanitizer.sanitize(request_json),
            queue_name=queue_name,
            priority=priority,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_task(self, task_id: str) -> Task:
        task = self.session.get(Task, task_id)
        if task is None or task.deleted_at is not None:
            raise KeyError("task_not_found")
        return task

    def list_tasks(self, *, status: str | None = None, experiment_id: str | None = None) -> list[Task]:
        stmt = select(Task).where(Task.deleted_at.is_(None)).order_by(Task.created_at.desc())
        if status:
            stmt = stmt.where(Task.status == status)
        if experiment_id:
            stmt = stmt.where(Task.experiment_id == experiment_id)
        return list(self.session.scalars(stmt).all())

    def mark_queued(self, task_id: str, celery_task_id: str | None = None) -> Task:
        task = self.get_task(task_id)
        task.status = "queued"
        task.celery_task_id = celery_task_id
        task.queued_at = datetime.now(timezone.utc)
        self._sync_experiment_status(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_running(self, task_id: str, provider_task_id: str | None = None) -> Task:
        task = self.get_task(task_id)
        task.status = "running"
        task.provider_task_id = provider_task_id
        task.started_at = datetime.now(timezone.utc)
        task.last_heartbeat_at = task.started_at
        self._sync_experiment_status(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def update_progress(self, task_id: str, progress: float, provider_status: str | None = None) -> Task:
        task = self.get_task(task_id)
        task.progress = max(0.0, min(1.0, progress))
        task.provider_status = provider_status
        task.last_heartbeat_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_succeeded(self, task_id: str, result_json: dict[str, Any] | None = None) -> Task:
        return self._finish(task_id, "succeeded", result_json=result_json)

    def mark_failed(self, task_id: str, error_json: dict[str, Any] | None = None) -> Task:
        return self._finish(task_id, "failed", error_json=error_json)

    def mark_timeout(self, task_id: str, error_json: dict[str, Any] | None = None) -> Task:
        return self._finish(task_id, "timeout", error_json=error_json)

    def request_cancel(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        task.cancel_requested = True
        task.cancel_requested_at = datetime.now(timezone.utc)
        if task.status in {"pending", "queued"}:
            task.status = "cancelled"
            task.finished_at = task.cancel_requested_at
            self._sync_experiment_status(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def mark_cancelled(self, task_id: str, error_json: dict[str, Any] | None = None) -> Task:
        return self._finish(task_id, "cancelled", error_json=error_json)

    def _finish(
        self,
        task_id: str,
        status: str,
        *,
        result_json: dict[str, Any] | None = None,
        error_json: dict[str, Any] | None = None,
    ) -> Task:
        if status not in TASK_STATUSES:
            raise ValueError("invalid_task_status")
        task = self.get_task(task_id)
        task.status = status
        task.result_json = self.sanitizer.sanitize(result_json)
        task.error_json = self.sanitizer.sanitize(error_json)
        task.finished_at = datetime.now(timezone.utc)
        task.progress = 1.0 if status == "succeeded" else task.progress
        self._sync_experiment_status(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def _sync_experiment_status(self, task: Task) -> None:
        if not task.experiment_id:
            return
        experiment = self._get_experiment(task.experiment_id)
        experiment.status = TASK_TO_EXPERIMENT_STATUS[task.status]
        experiment.result_mode = "async_task"
        if task.status in {"succeeded", "failed", "timeout", "cancelled"}:
            experiment.finished_at = datetime.now(timezone.utc)
            if task.result_json is not None:
                experiment.output_json = task.result_json
            if task.error_json is not None:
                experiment.error_json = task.error_json

    def _get_experiment(self, experiment_id: str) -> Experiment:
        experiment = self.session.get(Experiment, experiment_id)
        if experiment is None or experiment.deleted_at is not None:
            raise KeyError("experiment_not_found")
        return experiment
