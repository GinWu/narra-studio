from pathlib import Path

from backend.app.config import Settings
from backend.app.services.health_service import HealthService


def test_settings_paths_are_workspace_relative() -> None:
    settings = Settings(
        env="test",
        service_name="api",
        api_host="0.0.0.0",
        api_port=8000,
        database_url="sqlite:////tmp/aiwm-test.db",
        sqlite_dev_url="sqlite:////tmp/aiwm-test.db",
        redis_url="redis://redis:6379/0",
        workspace_root=Path("/tmp/aiwm-test-workspace"),
        log_level="INFO",
        enable_auto_migrations=False,
    )

    assert settings.assets_root == Path("/tmp/aiwm-test-workspace/assets")
    assert settings.uploads_root == Path("/tmp/aiwm-test-workspace/uploads")
    assert settings.thumbnails_root == Path("/tmp/aiwm-test-workspace/thumbnails")
    assert settings.exports_root == Path("/tmp/aiwm-test-workspace/exports")


def test_storage_health_creates_required_directories(tmp_path: Path) -> None:
    settings = Settings(
        env="test",
        service_name="api",
        api_host="0.0.0.0",
        api_port=8000,
        database_url="sqlite:////tmp/aiwm-test.db",
        sqlite_dev_url="sqlite:////tmp/aiwm-test.db",
        redis_url="redis://redis:6379/0",
        workspace_root=tmp_path,
        log_level="INFO",
        enable_auto_migrations=False,
    )

    assert HealthService(settings)._check_storage() == "ok"
    assert (tmp_path / "assets").is_dir()
    assert (tmp_path / "uploads").is_dir()
    assert (tmp_path / "thumbnails").is_dir()
    assert (tmp_path / "exports").is_dir()


def test_health_response_does_not_expose_workspace_path(tmp_path: Path) -> None:
    settings = Settings(
        env="test",
        service_name="api",
        api_host="0.0.0.0",
        api_port=8000,
        database_url="sqlite:////tmp/aiwm-test.db",
        sqlite_dev_url="sqlite:////tmp/aiwm-test.db",
        redis_url="redis://redis:6379/0",
        workspace_root=tmp_path,
        log_level="INFO",
        enable_auto_migrations=False,
    )

    result = HealthService(settings).check()

    assert result["status"] == "ok"
    assert result["database"] == "dev_sqlite_configured"
    assert result["workspace"] == "configured"
    assert "workspace_root" not in result
