from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.types import CapabilityResult, OutputFile
from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.services.asset_service import AssetService, DownloadedContent, FileService, StorageRepairService
from backend.app.services.experiment_service import ExperimentService


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


@pytest.fixture()
def settings(tmp_path: Path):
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


def test_asset_service_moves_temp_file_to_relative_workspace_path(db_session, settings, tmp_path):
    temp_file = tmp_path / "adapter-output.wav"
    temp_file.write_bytes(b"mock audio")
    experiment = ExperimentService(db_session).create_running(capability_type="tts", input_json={"text": "hi"})
    service = AssetService(db_session, settings=settings)

    refs = service.process_capability_result(
        experiment,
        CapabilityResult(
            status="success",
            output_files=[
                OutputFile(
                    file_role="audio_output",
                    file_type="audio",
                    mime_type="audio/wav",
                    extension="wav",
                    temp_path=str(temp_file),
                )
            ],
        ),
    )

    asset = service.get_asset(refs[0]["asset_id"])
    assert asset.relative_path.startswith("assets/audio/")
    assert not asset.relative_path.startswith("/")
    assert asset.source_experiment_id == experiment.id
    assert (settings.workspace_root / asset.relative_path).is_file()
    db_session.refresh(experiment)
    assert experiment.output_asset_refs_json == refs


def test_asset_service_downloads_source_url_with_injected_downloader(db_session, settings):
    experiment = ExperimentService(db_session).create_running(
        capability_type="image_generation",
        input_json={"prompt": "x"},
    )

    def downloader(url: str) -> DownloadedContent:
        assert url == "https://mock.local/output.png"
        return DownloadedContent(content=b"png-bytes", mime_type="image/png")

    service = AssetService(db_session, settings=settings, downloader=downloader)
    asset = service.create_from_output_file(
        experiment,
        OutputFile(
            file_role="image_output",
            file_type="image",
            extension="png",
            source_url="https://mock.local/output.png",
        ),
    )

    assert asset.mime_type == "image/png"
    assert asset.sha256 is not None
    assert (settings.workspace_root / asset.relative_path).read_bytes() == b"png-bytes"


def test_discarded_asset_downloads_but_deleted_asset_does_not(db_session, settings):
    asset = FileService(AssetService(db_session, settings=settings)).save_upload_bytes(
        asset_type="image",
        filename="upload.png",
        content=b"upload",
        mime_type="image/png",
    )
    service = AssetService(db_session, settings=settings)

    service.discard_asset(asset.id)
    assert service.get_download_path(asset.id).is_file()

    service.delete_asset(asset.id)
    with pytest.raises(KeyError):
        service.get_asset(asset.id)


def test_storage_repair_reports_missing_files(db_session, settings):
    asset = FileService(AssetService(db_session, settings=settings)).save_upload_bytes(
        asset_type="text",
        filename="note.txt",
        content=b"hello",
        mime_type="text/plain",
    )
    (settings.workspace_root / asset.relative_path).unlink()

    report = StorageRepairService(AssetService(db_session, settings=settings)).check_assets()

    assert report["checked_count"] == 1
    assert report["missing_asset_ids"] == [asset.id]
