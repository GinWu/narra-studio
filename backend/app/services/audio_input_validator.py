"""Audio asset validation for STT and voice clone workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from backend.app.config import Settings, get_settings
from backend.app.db.models import Asset


class AudioInputValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class AudioValidationResult:
    asset: Asset
    warnings: list[str]


class AudioInputValidator:
    SUPPORTED_MIME_TYPES = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mp4",
        "audio/m4a",
        "audio/ogg",
        "audio/webm",
    }
    MAX_AUDIO_SIZE_BYTES = 100 * 1024 * 1024
    MAX_CLONE_SAMPLE_COUNT = 10
    MAX_CLONE_TOTAL_DURATION_MS = 30 * 60 * 1000

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    def validate_audio_asset(self, asset_id: str) -> AudioValidationResult:
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise AudioInputValidationError("AUDIO_INPUT_NOT_FOUND", "Audio asset not found.")
        if asset.status == "deleted":
            raise AudioInputValidationError("AUDIO_INPUT_NOT_FOUND", "Audio asset is deleted.")
        if asset.asset_type != "audio":
            raise AudioInputValidationError("AUDIO_INPUT_INVALID", "Asset must be an audio asset.")
        if asset.mime_type and asset.mime_type.lower() not in self.SUPPORTED_MIME_TYPES:
            raise AudioInputValidationError("AUDIO_INPUT_UNSUPPORTED_MIME", "Audio MIME type is not supported.")
        if asset.size_bytes is not None and asset.size_bytes > self.MAX_AUDIO_SIZE_BYTES:
            raise AudioInputValidationError("AUDIO_INPUT_TOO_LARGE", "Audio file is too large.")

        path = self._asset_path(asset)
        if not path.is_file():
            raise AudioInputValidationError("AUDIO_INPUT_NOT_FOUND", "Audio file is missing from storage.")

        warnings: list[str] = []
        if asset.duration_ms is None:
            warnings.append("duration_unavailable")
        return AudioValidationResult(asset=asset, warnings=warnings)

    def validate_voice_clone_assets(self, asset_ids: Iterable[str]) -> list[AudioValidationResult]:
        ids = [asset_id for asset_id in asset_ids if asset_id]
        if not ids:
            raise AudioInputValidationError("AUDIO_INPUT_NOT_FOUND", "At least one reference audio asset is required.")
        if len(ids) > self.MAX_CLONE_SAMPLE_COUNT:
            raise AudioInputValidationError("AUDIO_INPUT_INVALID", "Too many voice clone samples.")
        results = [self.validate_audio_asset(asset_id) for asset_id in ids]
        known_duration = sum(result.asset.duration_ms or 0 for result in results)
        if known_duration > self.MAX_CLONE_TOTAL_DURATION_MS:
            raise AudioInputValidationError("AUDIO_INPUT_TOO_LARGE", "Voice clone samples are too long.")
        return results

    def _asset_path(self, asset: Asset) -> Path:
        path = self.settings.workspace_root / asset.relative_path
        root = self.settings.workspace_root.resolve()
        resolved_parent = path.parent.resolve()
        if root not in [resolved_parent, *resolved_parent.parents]:
            raise AudioInputValidationError("AUDIO_INPUT_INVALID", "Asset path escapes workspace.")
        return path
