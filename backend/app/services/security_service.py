"""Security sanitization and safe project export manifests."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.orm import Session

from backend.app.db.models import Asset, ProjectItem


class SanitizerService:
    sensitive_markers = ("authorization", "api_key", "apikey", "token", "secret", "credential", "password", "bearer")

    def sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._sanitize_key_value(key, item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.sanitize(item) for item in value]
        if isinstance(value, str):
            return self.sanitize_string(value)
        return value

    def sanitize_source_url(self, source_url: str | None) -> str | None:
        if not source_url:
            return None
        parsed = urlsplit(source_url)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

    def sanitize_string(self, value: str) -> str:
        lowered = value.lower()
        if "bearer " in lowered or "api_key=" in lowered or "token=" in lowered or "signature=" in lowered:
            return "[REDACTED]"
        if value.startswith("/") and ("/workspace/" in value or "/app/" in value or "/tmp/" in value):
            return "[REDACTED_PATH]"
        return value

    def _sanitize_key_value(self, key: str, value: Any) -> Any:
        lowered = key.lower()
        if any(marker in lowered for marker in self.sensitive_markers):
            return "[REDACTED]"
        if "source_url" in lowered or "signed_url" in lowered:
            return self.sanitize_source_url(str(value)) if value is not None else None
        return self.sanitize(value)


class ProjectExportService:
    def __init__(self, session: Session, sanitizer: SanitizerService | None = None) -> None:
        self.session = session
        self.sanitizer = sanitizer or SanitizerService()

    def build_manifest(self, project_id: str, *, include_discarded: bool = False) -> dict[str, Any]:
        from backend.app.services.project_service import ProjectService
        project_service = ProjectService(self.session)
        project = project_service.get_project(project_id)
        items = project_service.list_items(project_id)
        manifest_items: list[dict[str, Any]] = []
        for item in items:
            exported = self._export_item(item, include_discarded=include_discarded)
            if exported is not None:
                manifest_items.append(exported)
        return self.sanitizer.sanitize(
            {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "metadata_json": project.metadata_json,
                },
                "items": manifest_items,
            }
        )

    def _export_item(self, item: ProjectItem, *, include_discarded: bool) -> dict[str, Any] | None:
        payload: dict[str, Any] = {
            "id": item.id,
            "item_type": item.item_type,
            "target_id": item.target_id,
            "role": item.role,
            "sort_order": item.sort_order,
            "metadata_json": item.metadata_json,
        }
        if item.item_type == "asset":
            asset = self.session.get(Asset, item.target_id)
            if asset is None or asset.status == "deleted":
                return None
            if asset.status == "discarded" and not include_discarded:
                return None
            payload["asset"] = {
                "id": asset.id,
                "asset_type": asset.asset_type,
                "status": asset.status,
                "relative_path": asset.relative_path,
                "mime_type": asset.mime_type,
                "sha256": asset.sha256,
            }
        return payload
