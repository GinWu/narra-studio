from __future__ import annotations

import logging

from backend.app.capabilities.bootstrap import build_default_adapter_registry
from backend.app.db.session import SessionLocal
from backend.app.services.security_service import SanitizerService
from backend.app.services.task_service import TaskService
from backend.app.services.video_lab_service import VideoLabService
from backend.app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def execute_video_generation(task_id: str) -> dict[str, str]:
    sanitizer = SanitizerService()
    with SessionLocal() as session:
        try:
            outcome = VideoLabService(session, build_default_adapter_registry()).run_video_task(task_id)
            return sanitizer.sanitize(
                {
                    "task_id": task_id,
                    "experiment_id": outcome.experiment.id,
                    "status": outcome.experiment.status,
                }
            )
        except Exception:
            logger.exception("video task execution failed")
            try:
                TaskService(session).mark_failed(
                    task_id,
                    error_json={
                        "error_type": "worker_error",
                        "message": "Video worker failed.",
                    },
                )
            except Exception:
                logger.exception("failed to mark video task as failed")
            raise


if celery_app is not None:

    @celery_app.task(name="video.generate")
    def generate_video(task_id: str) -> dict[str, str]:
        return execute_video_generation(task_id)


def enqueue_video_generation(task_id: str) -> str:
    if celery_app is None:
        raise RuntimeError("celery_unavailable")
    result = celery_app.send_task("video.generate", args=[task_id], queue="video")
    return str(result.id)
