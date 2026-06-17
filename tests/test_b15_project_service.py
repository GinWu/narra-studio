from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.services.asset_service import AssetService, FileService
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.project_service import ProjectService


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


def test_project_can_reference_same_asset_without_replacing_asset_fact(db_session):
    session, tmp_path = db_session
    service = ProjectService(session)
    first = service.create_project({"name": "Project A"})
    second = service.create_project({"name": "Project B"})
    asset = FileService(AssetService(session, settings=_settings(tmp_path))).save_upload_bytes(
        asset_type="image",
        filename="frame.png",
        content=b"frame",
        mime_type="image/png",
    )

    first_item = service.add_item(project_id=first.id, item_type="asset", target_id=asset.id)
    second_item = service.add_item(project_id=second.id, item_type="asset", target_id=asset.id)
    session.refresh(asset)

    assert first_item.target_id == asset.id
    assert second_item.target_id == asset.id
    assert asset.project_id == first.id


def test_script_versions_and_shots_are_project_items(db_session):
    session, _ = db_session
    service = ProjectService(session)
    project = service.create_project({"name": "Video"})
    script = service.create_script_version(project_id=project.id, title="v1", content="hello")
    shot = service.create_shot(project_id=project.id, name="Shot 1", script_version_id=script.id)
    items = service.list_items(project.id)

    assert script.version == 1
    assert shot.script_version_id == script.id
    assert {item.item_type for item in items} == {"script_version", "shot"}


def test_shot_asset_selection_records_usage_relation(db_session):
    session, tmp_path = db_session
    service = ProjectService(session)
    project = service.create_project({"name": "Video"})
    shot = service.create_shot(project_id=project.id, name="Shot 1")
    asset = FileService(AssetService(session, settings=_settings(tmp_path))).save_upload_bytes(
        asset_type="video",
        filename="clip.mp4",
        content=b"clip",
        mime_type="video/mp4",
    )

    updated = service.select_shot_asset(shot.id, asset_type="video", asset_id=asset.id)
    session.refresh(asset)

    assert updated.selected_video_asset_id == asset.id
    assert asset.project_id == project.id


def test_project_item_can_reference_experiment(db_session):
    session, _ = db_session
    service = ProjectService(session)
    project = service.create_project({"name": "Workbench"})
    experiment = ExperimentService(session).create_running(capability_type="tts", input_json={"text": "hi"})
    item = service.add_item(project_id=project.id, item_type="experiment", target_id=experiment.id)

    assert item.item_type == "experiment"
    assert item.target_id == experiment.id


def test_shot_update(db_session):
    session, _ = db_session
    service = ProjectService(session)
    project = service.create_project({"name": "Video"})
    shot = service.create_shot(project_id=project.id, name="Shot 1")
    
    updated = service.update_shot(shot.id, {"voiceover_text": "Updated text", "metadata_json": {"voice_profile_id": "test_vp"}})
    assert updated.voiceover_text == "Updated text"
    assert updated.metadata_json == {"voice_profile_id": "test_vp"}

