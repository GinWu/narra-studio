from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.services.asset_service import AssetService, FileService
from backend.app.services.project_service import ProjectService
from backend.app.services.security_service import ProjectExportService, SanitizerService


def test_sanitizer_redacts_secrets_paths_and_signed_url_queries():
    sanitizer = SanitizerService()
    payload = sanitizer.sanitize(
        {
            "Authorization": "Bearer abc",
            "nested": {"api_key": "secret", "path": "/app/workspace/assets/a.png"},
            "source_url": "https://provider.local/file.png?signature=abc&token=def",
        }
    )

    assert payload["Authorization"] == "[REDACTED]"
    assert payload["nested"]["api_key"] == "[REDACTED]"
    assert payload["nested"]["path"] == "[REDACTED_PATH]"
    assert payload["source_url"] == "https://provider.local/file.png"


def test_project_export_manifest_excludes_discarded_assets_and_uses_relative_paths(tmp_path: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    settings = Settings(
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
    with Session() as session:
        project = ProjectService(session).create_project({"name": "Export"})
        active = FileService(AssetService(session, settings=settings)).save_upload_bytes(
            asset_type="image",
            filename="active.png",
            content=b"active",
            mime_type="image/png",
        )
        discarded = FileService(AssetService(session, settings=settings)).save_upload_bytes(
            asset_type="image",
            filename="discarded.png",
            content=b"discarded",
            mime_type="image/png",
        )
        ProjectService(session).add_item(project_id=project.id, item_type="asset", target_id=active.id)
        ProjectService(session).add_item(project_id=project.id, item_type="asset", target_id=discarded.id)
        AssetService(session, settings=settings).discard_asset(discarded.id)

        manifest = ProjectExportService(session).build_manifest(project.id)
        exported_asset_ids = [item["target_id"] for item in manifest["items"]]

        assert active.id in exported_asset_ids
        assert discarded.id not in exported_asset_ids
        assert manifest["items"][0]["asset"]["relative_path"].startswith("assets/")
        assert not manifest["items"][0]["asset"]["relative_path"].startswith("/")
    Base.metadata.drop_all(engine)
