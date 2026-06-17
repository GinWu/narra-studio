from __future__ import annotations

from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.services.health_service import HealthService


router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return HealthService(settings).check()


@router.get("/info")
def info() -> dict[str, object]:
    settings = get_settings()
    return {
        "service": "narra-studio-api",
        "env": settings.env,
        "service_name": settings.service_name,
        "workspace": "configured",
        "docker_first": True,
        "database_default": "postgresql",
        "sqlite_profile": "dev_only",
    }
