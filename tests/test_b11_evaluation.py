from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.services.asset_service import AssetService, FileService
from backend.app.services.evaluation_service import CompareService, EvaluationService, stable_compare_group_id
from backend.app.services.experiment_service import ExperimentService


@pytest.fixture()
def db_session(tmp_path: Path):
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


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        service_name="api",
        api_host="0.0.0.0",
        api_port=8000,
        database_url="sqlite://",
        sqlite_dev_url="sqlite://",
        redis_url="redis://redis:6379/0",
        workspace_root=tmp_path,
        log_level="INFO",
        enable_auto_migrations=False,
    )


def test_evaluation_upsert_does_not_duplicate_active_exvaluation(db_session):
    session, _ = db_session
    exp = ExperimentService(session).create_running(capability_type="tts", input_json={"text": "hi"})
    service = EvaluationService(session)

    first = service.upsert_evaluation(target_type="experiment", target_id=exp.id, dimension="clarity", score=3)
    second = service.upsert_evaluation(target_type="experiment", target_id=exp.id, dimension="clarity", score=5)

    assert first.id == second.id
    assert second.score == 5
    assert len(service.list_evaluations(target_type="experiment", target_id=exp.id)) == 1


def test_asset_rating_cache_uses_usability_then_average(db_session):
    session, tmp_path = db_session
    asset = FileService(AssetService(session, settings=_settings(tmp_path))).save_upload_bytes(
        asset_type="image",
        filename="x.png",
        content=b"x",
        mime_type="image/png",
    )
    service = EvaluationService(session)
    service.upsert_evaluation(target_type="asset", target_id=asset.id, dimension="美感", score=4)
    session.refresh(asset)
    assert asset.rating == 4

    service.upsert_evaluation(target_type="asset", target_id=asset.id, dimension="可用性", score=2)
    session.refresh(asset)
    assert asset.rating == 2


def test_compare_group_best_does_not_modify_experiment_best(db_session):
    session, _ = db_session
    first = ExperimentService(session).create_running(capability_type="tts", input_json={"text": "a"})
    second = ExperimentService(session).create_running(capability_type="tts", input_json={"text": "b"})
    service = EvaluationService(session)
    group_id = stable_compare_group_id([first.id, second.id])

    first_eval = service.upsert_evaluation(
        target_type="experiment",
        target_id=first.id,
        dimension="overall",
        score=5,
        compare_group_id=group_id,
        is_best=True,
    )
    second_eval = service.upsert_evaluation(
        target_type="experiment",
        target_id=second.id,
        dimension="overall",
        score=4,
        compare_group_id=group_id,
        is_best=True,
    )
    session.refresh(first_eval)
    session.refresh(first)
    session.refresh(second)

    assert first_eval.is_best is False
    assert second_eval.is_best is True
    assert first.is_best is False
    assert second.is_best is False


def test_compare_service_returns_experiment_evaluations(db_session):
    session, _ = db_session
    exp = ExperimentService(session).create_running(capability_type="image_generation", input_json={"prompt": "x"})
    EvaluationService(session).upsert_evaluation(
        target_type="experiment",
        target_id=exp.id,
        dimension="overall",
        score=4,
    )

    items = CompareService(session).get_compare_items([exp.id])

    assert items[0]["experiment_id"] == exp.id
    assert items[0]["evaluations"][0]["score"] == 4
