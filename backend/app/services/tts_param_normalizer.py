"""TTS parameter normalization, including TDS-13 VoiceProfile support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from backend.app.db.models import Model
from backend.app.services.voice_profile_service import VoiceProfileService, VoiceProfileValidation


@dataclass(frozen=True)
class NormalizedTtsParams:
    params: dict[str, Any]
    voice_profile_validation: VoiceProfileValidation | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TTSParamNormalizer:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.voice_profiles = VoiceProfileService(session)

    def normalize(
        self,
        *,
        model: Model,
        base_params: dict[str, Any] | None = None,
        voice_config: dict[str, Any] | None = None,
        voice: str | None = None,
        voice_id: str | None = None,
        commercial_use: bool = False,
        explicit_confirm: bool = False,
    ) -> NormalizedTtsParams:
        params = dict(model.default_params_json or {})
        params.update(base_params or {})
        config = dict(voice_config or {})
        if voice_id:
            config["voice_id"] = voice_id
        if voice:
            config["voice"] = voice

        voice_profile_id = config.get("voice_profile_id")
        if voice_profile_id:
            validation = self.voice_profiles.validate_voice_profile_for_tts(
                voice_profile_id=str(voice_profile_id),
                model=model,
                commercial_use=commercial_use,
                explicit_confirm=explicit_confirm,
            )
            profile = validation.voice_profile
            params["voice_id"] = profile.voice_id
            params["voice_profile_id"] = profile.id
            params["voice_source"] = "voice_profile"
            return NormalizedTtsParams(
                params=params,
                voice_profile_validation=validation,
                metadata={
                    "voice_profile_id": profile.id,
                    "voice_id": profile.voice_id,
                    "voice_source": "voice_profile",
                    "voice_profile_warnings": validation.warnings,
                },
            )

        if config.get("voice_id"):
            params["voice_id"] = config["voice_id"]
            params["voice_source"] = "voice_id"
            return NormalizedTtsParams(params=params, metadata={"voice_source": "voice_id"})

        if config.get("voice"):
            params["voice"] = config["voice"]
            params["voice_source"] = "voice"
            return NormalizedTtsParams(params=params, metadata={"voice_source": "voice"})

        if params.get("voice"):
            params["voice_source"] = "model_default"
            return NormalizedTtsParams(params=params, metadata={"voice_source": "model_default"})

        return NormalizedTtsParams(params=params, metadata={"voice_source": "unspecified"})
