from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str
    service_name: str
    api_host: str
    api_port: int
    database_url: str
    sqlite_dev_url: str
    redis_url: str
    workspace_root: Path
    log_level: str
    enable_auto_migrations: bool

    @property
    def assets_root(self) -> Path:
        return self.workspace_root / "assets"

    @property
    def uploads_root(self) -> Path:
        return self.workspace_root / "uploads"

    @property
    def thumbnails_root(self) -> Path:
        return self.workspace_root / "thumbnails"

    @property
    def exports_root(self) -> Path:
        return self.workspace_root / "exports"


def get_settings() -> Settings:
    return Settings(
        env=os.getenv("AIWM_ENV", "development"),
        service_name=os.getenv("AIWM_SERVICE_NAME", "api"),
        api_host=os.getenv("AIWM_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("AIWM_API_PORT", "8000")),
        database_url=os.getenv(
            "AIWM_DATABASE_URL",
            "postgresql://aiwm:aiwm_dev_password@db:5432/aiwm",
        ),
        sqlite_dev_url=os.getenv("AIWM_SQLITE_DEV_URL", "sqlite:////tmp/aiwm-dev.db"),
        redis_url=os.getenv("AIWM_REDIS_URL", "redis://redis:6379/0"),
        workspace_root=Path(os.getenv("AIWM_WORKSPACE_ROOT", "/app/workspace")),
        log_level=os.getenv("AIWM_LOG_LEVEL", "INFO"),
        enable_auto_migrations=_bool_from_env("AIWM_ENABLE_AUTO_MIGRATIONS", False),
    )

