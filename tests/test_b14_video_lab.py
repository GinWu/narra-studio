from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import MockAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.db.base import Base
from backend.app.db.models import Asset, CostRecord, Experiment
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.provider_service import ProviderService
from backend.app.services.task_service import TaskService
from backend.app.services.video_lab_service import VideoGenerationInput, VideoLabService, VideoLabValidationError


@pytest.fixture()
def db_session(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("AIWM_WORKSPACE_ROOT", str(tmp_path))
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with Session() as session:
        yield session, tmp_path
    Base.metadata.drop_all(engine)


def _video_service(session):
    provider = ProviderService(session).create_provider(
        {
            "name": "mock",
            "provider_type": "mock",
            "credential_source": "none",
            "enabled": True,
            "status": "active",
            "adapter_name": "mock",
        }
    )
    ModelRegistryService(session).seed_mock_models(provider.id)
    registry = AdapterRegistry()
    registry.register(MockAdapter())
    return VideoLabService(session, registry)


def test_video_lab_async_mock_run_creates_task_experiment_and_asset(db_session):
    session, tmp_path = db_session
    result = _video_service(session).create_video_task(
        VideoGenerationInput(prompt="a clip", duration_seconds=2),
        run_immediately=True,
    )
    task = TaskService(session).get_task(result.task_id)
    experiment = session.get(Experiment, result.experiment_id)

    assert task.status == "succeeded"
    assert experiment.status == "success"
    assert experiment.result_mode == "async_task"
    asset = session.get(Asset, experiment.output_asset_refs_json[0]["asset_id"])
    assert asset.asset_type == "video"
    assert (tmp_path / asset.relative_path).is_file()


def test_video_lab_default_path_enqueues_task_without_inline_run(db_session, monkeypatch):
    session, _ = db_session
    enqueued_task_ids: list[str] = []

    def fake_enqueue(task_id: str) -> str:
        enqueued_task_ids.append(task_id)
        return "celery-video-1"

    monkeypatch.setattr("backend.app.services.video_lab_service.enqueue_video_generation", fake_enqueue)

    result = _video_service(session).create_video_task(VideoGenerationInput(prompt="queued clip"))
    task = TaskService(session).get_task(result.task_id)
    experiment = session.get(Experiment, result.experiment_id)

    assert enqueued_task_ids == [task.id]
    assert task.status == "queued"
    assert task.celery_task_id == "celery-video-1"
    assert experiment.status == "pending"
    assert experiment.result_mode == "async_task"


def test_video_lab_queue_failure_marks_task_and_experiment_failed(db_session, monkeypatch):
    session, _ = db_session

    def fail_enqueue(task_id: str) -> str:
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr("backend.app.services.video_lab_service.enqueue_video_generation", fail_enqueue)

    result = _video_service(session).create_video_task(VideoGenerationInput(prompt="queued clip"))
    task = TaskService(session).get_task(result.task_id)
    experiment = session.get(Experiment, result.experiment_id)

    assert task.status == "failed"
    assert task.error_json["error_type"] == "queue_submit_failed"
    assert experiment.status == "failed"
    assert experiment.error_json["error_type"] == "queue_submit_failed"


def test_video_worker_task_executes_queued_video_task(db_session, monkeypatch):
    session, tmp_path = db_session
    monkeypatch.setattr("backend.app.services.video_lab_service.enqueue_video_generation", lambda task_id: "celery-video-2")
    result = _video_service(session).create_video_task(VideoGenerationInput(prompt="worker clip"))

    from backend.app.tasks import video_tasks

    WorkerSession = sessionmaker(bind=session.get_bind(), autoflush=False, autocommit=False, expire_on_commit=False)
    monkeypatch.setattr(video_tasks, "SessionLocal", WorkerSession)

    video_tasks.execute_video_generation(result.task_id)
    session.expire_all()
    task = TaskService(session).get_task(result.task_id)
    experiment = session.get(Experiment, result.experiment_id)

    assert task.status == "succeeded"
    assert experiment.status == "success"
    asset = session.get(Asset, experiment.output_asset_refs_json[0]["asset_id"])
    assert asset.asset_type == "video"
    assert (tmp_path / asset.relative_path).is_file()
    assert session.query(CostRecord).filter_by(experiment_id=experiment.id).count() == 1


def test_video_lab_validation(db_session):
    session, _ = db_session
    service = _video_service(session)
    with pytest.raises(VideoLabValidationError):
        service.create_video_task(VideoGenerationInput(prompt=""))
    with pytest.raises(VideoLabValidationError):
        service.create_video_task(VideoGenerationInput(prompt="x", duration_seconds=120))
