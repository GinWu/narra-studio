from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.task_service import TASK_TO_EXPERIMENT_STATUS, TaskService


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with Session() as session:
        yield session
    Base.metadata.drop_all(engine)


def test_task_status_maps_to_experiment_status(db_session):
    exp = ExperimentService(db_session).create_running(
        capability_type="video_generation",
        input_json={"prompt": "clip"},
        result_mode="async_task",
    )
    service = TaskService(db_session)

    for task_status, experiment_status in TASK_TO_EXPERIMENT_STATUS.items():
        task = service.create_task(task_type="video_generation", experiment_id=exp.id)
        if task_status == "queued":
            task = service.mark_queued(task.id)
        elif task_status == "running":
            task = service.mark_running(task.id, provider_task_id="provider_1")
        elif task_status == "succeeded":
            task = service.mark_succeeded(task.id, result_json={"ok": True})
        elif task_status == "failed":
            task = service.mark_failed(task.id, error_json={"error_type": "failed"})
        elif task_status == "timeout":
            task = service.mark_timeout(task.id, error_json={"error_type": "timeout"})
        elif task_status == "cancelled":
            task = service.mark_cancelled(task.id, error_json={"error_type": "cancelled"})
        db_session.refresh(exp)
        assert task.status == task_status
        assert exp.status == experiment_status
        assert exp.result_mode == "async_task"


def test_pending_or_queued_task_can_be_cancelled(db_session):
    exp = ExperimentService(db_session).create_running(
        capability_type="video_generation",
        input_json={"prompt": "clip"},
        result_mode="async_task",
    )
    service = TaskService(db_session)
    task = service.create_task(task_type="video_generation", experiment_id=exp.id)
    task = service.mark_queued(task.id)
    task = service.request_cancel(task.id)
    db_session.refresh(exp)

    assert task.status == "cancelled"
    assert task.cancel_requested is True
    assert exp.status == "cancelled"


def test_running_cancel_request_sets_flag_without_forcing_cancelled(db_session):
    exp = ExperimentService(db_session).create_running(
        capability_type="video_generation",
        input_json={"prompt": "clip"},
        result_mode="async_task",
    )
    service = TaskService(db_session)
    task = service.create_task(task_type="video_generation", experiment_id=exp.id)
    service.mark_running(task.id)
    task = service.request_cancel(task.id)
    db_session.refresh(exp)

    assert task.status == "running"
    assert task.cancel_requested is True
    assert exp.status == "running"


def test_task_service_sanitizes_persisted_payloads(db_session):
    exp = ExperimentService(db_session).create_running(
        capability_type="video_generation",
        input_json={"prompt": "clip"},
        result_mode="async_task",
    )
    service = TaskService(db_session)
    task = service.create_task(
        task_type="video_generation",
        experiment_id=exp.id,
        request_json={
            "Authorization": "Bearer secret",
            "signed_url": "https://provider.local/file.mp4?token=secret",
            "path": "/tmp/provider-output.mp4",
        },
    )

    assert task.request_json["Authorization"] == "[REDACTED]"
    assert task.request_json["signed_url"] == "https://provider.local/file.mp4"
    assert task.request_json["path"] == "[REDACTED_PATH]"

    task = service.mark_failed(
        task.id,
        error_json={
            "api_key": "secret",
            "source_url": "https://provider.local/error.json?signature=secret",
        },
    )

    assert task.error_json["api_key"] == "[REDACTED]"
    assert task.error_json["source_url"] == "https://provider.local/error.json"
