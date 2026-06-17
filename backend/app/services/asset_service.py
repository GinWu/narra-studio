"""Asset fact creation, final workspace storage, and download rules."""

from __future__ import annotations

import hashlib
import mimetypes
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.capabilities.types import CapabilityResult, OutputFile
from backend.app.config import Settings, get_settings
from backend.app.db.models import Asset, Experiment
from backend.app.utils.ids import new_id


class AssetServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class DownloadedContent:
    content: bytes
    mime_type: str | None = None


Downloader = Callable[[str], DownloadedContent]


class AssetService:
    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        downloader: Downloader | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.downloader = downloader or self._download_source_url

    def process_capability_result(self, experiment: Experiment, result: CapabilityResult) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for output in result.output_files:
            try:
                asset = self.create_from_output_file(experiment, output)
                refs.append(
                    {
                        "asset_id": asset.id,
                        "asset_type": asset.asset_type,
                        "download_url": f"/api/assets/{asset.id}/download",
                    }
                )
            except Exception as exc:
                errors.append({"file_role": output.file_role, "error": "asset_create_failed"})
        from backend.app.services.experiment_service import ExperimentService
        ExperimentService(self.session).update_output_asset_refs(experiment.id, refs)
        if errors:
            experiment.error_json = {"error_type": "asset_partial_failure", "items": errors}
            self.session.commit()
        return refs

    def create_from_output_file(self, experiment: Experiment, output: OutputFile) -> Asset:
        asset_id = new_id("ast")
        extension = self._extension(output)
        relative_path = self._relative_asset_path(output.file_type, asset_id, extension)
        final_path = self._absolute_path(relative_path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        if output.temp_path:
            temp_path = Path(output.temp_path)
            if not temp_path.is_file():
                raise AssetServiceError("Temporary output file is missing.")
            shutil.move(str(temp_path), final_path)
            mime_type = output.mime_type or mimetypes.guess_type(final_path.name)[0]
        elif output.source_url:
            downloaded = self.downloader(output.source_url)
            final_path.write_bytes(downloaded.content)
            mime_type = output.mime_type or downloaded.mime_type or mimetypes.guess_type(final_path.name)[0]
        else:
            raise AssetServiceError("Output file must include temp_path or source_url.")

        sha256, size_bytes = self._file_digest(final_path)
        asset = Asset(
            id=asset_id,
            asset_type=output.file_type,
            status="active",
            relative_path=relative_path,
            filename=final_path.name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256=sha256,
            width=output.width,
            height=output.height,
            duration_ms=int(output.duration_seconds * 1000) if output.duration_seconds is not None else None,
            source_experiment_id=experiment.id,
            project_id=experiment.project_id,
            metadata_json={"file_role": output.file_role, **output.metadata},
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def list_assets(
        self,
        *,
        asset_type: str | None = None,
        status: str | None = None,
        project_id: str | None = None,
        source_experiment_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Asset]:
        stmt = select(Asset).where(Asset.deleted_at.is_(None)).order_by(Asset.created_at.desc())
        if asset_type:
            stmt = stmt.where(Asset.asset_type == asset_type)
        if status:
            stmt = stmt.where(Asset.status == status)
        if project_id:
            stmt = stmt.where(Asset.project_id == project_id)
        if source_experiment_id:
            stmt = stmt.where(Asset.source_experiment_id == source_experiment_id)
        return list(self.session.scalars(stmt.limit(limit).offset(offset)).all())

    def get_asset(self, asset_id: str) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise KeyError("asset_not_found")
        return asset

    def get_download_path(self, asset_id: str) -> Path:
        asset = self.get_asset(asset_id)
        if asset.status == "deleted":
            raise PermissionError("deleted_asset_not_downloadable")
        path = self._absolute_path(asset.relative_path)
        if not path.is_file():
            raise FileNotFoundError("asset_file_missing")
        return path

    def discard_asset(self, asset_id: str) -> Asset:
        asset = self.get_asset(asset_id)
        asset.status = "discarded"
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def delete_asset(self, asset_id: str) -> Asset:
        asset = self.get_asset(asset_id)
        asset.status = "deleted"
        asset.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def _relative_asset_path(self, asset_type: str, asset_id: str, extension: str) -> str:
        today = datetime.now(timezone.utc)
        safe_type = asset_type if asset_type in {"audio", "image", "video", "text", "metadata", "other"} else "other"
        return f"assets/{safe_type}/{today:%Y/%m/%d}/{asset_id}.{extension}"

    def _absolute_path(self, relative_path: str) -> Path:
        path = self.settings.workspace_root / relative_path
        root = self.settings.workspace_root.resolve()
        resolved_parent = path.parent.resolve()
        if root not in [resolved_parent, *resolved_parent.parents]:
            raise AssetServiceError("Asset path escapes workspace.")
        return path

    def _extension(self, output: OutputFile) -> str:
        extension = output.extension or mimetypes.guess_extension(output.mime_type or "") or "bin"
        return extension.lstrip(".").replace("/", "_")

    def _file_digest(self, path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        return digest.hexdigest(), size

    def _download_source_url(self, source_url: str) -> DownloadedContent:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(source_url)
            response.raise_for_status()
            return DownloadedContent(
                content=response.content,
                mime_type=response.headers.get("content-type"),
            )


class FileService:
    def __init__(self, asset_service: AssetService) -> None:
        self.asset_service = asset_service

    def save_upload_bytes(
        self,
        *,
        asset_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None = None,
        project_id: str | None = None,
    ) -> Asset:
        suffix = Path(filename).suffix.lstrip(".") or "bin"
        temp_dir = Path(self.asset_service.settings.uploads_root)
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"{new_id('upload')}.{suffix}"
        temp_path.write_bytes(content)
        experiment = Experiment(
            id=new_id("exp"),
            capability_type="manual_upload",
            status="success",
            result_mode="sync",
            input_json={"filename": filename},
            project_id=project_id,
        )
        self.asset_service.session.add(experiment)
        self.asset_service.session.commit()
        return self.asset_service.create_from_output_file(
            experiment,
            OutputFile(
                file_role="upload",
                file_type=asset_type,
                mime_type=mime_type,
                extension=suffix,
                temp_path=str(temp_path),
            ),
        )


class StorageRepairService:
    def __init__(self, asset_service: AssetService) -> None:
        self.asset_service = asset_service

    def check_assets(self) -> dict[str, Any]:
        assets = self.asset_service.list_assets(limit=10000)
        missing: list[str] = []
        checksum_mismatch: list[str] = []
        for asset in assets:
            if asset.status == "deleted":
                continue
            path = self.asset_service.settings.workspace_root / asset.relative_path
            if not path.is_file():
                missing.append(asset.id)
                continue
            sha256, _ = self.asset_service._file_digest(path)
            if asset.sha256 and sha256 != asset.sha256:
                checksum_mismatch.append(asset.id)
        return {
            "checked_count": len(assets),
            "missing_asset_ids": missing,
            "checksum_mismatch_asset_ids": checksum_mismatch,
        }
