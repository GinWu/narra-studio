from __future__ import annotations

from backend.app.config import get_settings

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    Celery = None  # type: ignore


def create_celery_app():
    if Celery is None:
        return None
    settings = get_settings()
    return Celery(
        "narra_studio",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["backend.app.tasks.video_tasks"],
    )


celery_app = create_celery_app()
