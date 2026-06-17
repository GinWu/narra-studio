"""Voice Lab backend workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.db.models import Asset
from backend.app.services.asset_service import AssetService
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunOutcome, CapabilityRunService
from backend.app.services.cost_service import CostService
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.prompt_template_service import PromptTemplateService
from backend.app.services.tts_param_normalizer import TTSParamNormalizer


class VoiceLabValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TtsRunInput:
    text: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    voice: str | None = None
    voice_id: str | None = None
    voice_config: dict[str, Any] | None = None
    speed: float | None = None
    response_format: str | None = None
    params_json: dict[str, Any] | None = None
    commercial_use: bool = False
    explicit_confirm: bool = False
    project_id: str | None = None
    shot_id: str | None = None


class VoiceLabService:
    MAX_TEXT_LENGTH = 10000

    def __init__(self, session: Session, adapter_registry: AdapterRegistry) -> None:
        self.session = session
        self.adapter_registry = adapter_registry

    def run_tts(self, payload: TtsRunInput) -> CapabilityRunOutcome:
        final_text = self._resolve_text(payload)
        model = (
            ModelRegistryService(self.session).get_model(payload.model_id)
            if payload.model_id
            else ModelRegistryService(self.session).get_default_model("tts")
        )
        normalized = TTSParamNormalizer(self.session).normalize(
            model=model,
            base_params=payload.params_json,
            voice_config=payload.voice_config,
            voice=payload.voice,
            voice_id=payload.voice_id,
            commercial_use=payload.commercial_use,
            explicit_confirm=payload.explicit_confirm,
        )
        params = dict(normalized.params)
        if payload.speed is not None:
            if not 0.5 <= payload.speed <= 2.0:
                raise VoiceLabValidationError("speed must be between 0.5 and 2.0")
            params["speed"] = payload.speed
        if payload.response_format:
            params["response_format"] = payload.response_format

        outcome = CapabilityRunService(
            self.session,
            self.adapter_registry,
            asset_processor=AssetService(self.session),
            cost_recorder=CostService(self.session),
        ).run(
            CapabilityRunCommand(
                capability_type="tts",
                input_json={"text": final_text},
                params_json=params,
                model_id=model.id,
                prompt_template_id=payload.prompt_template_id,
                project_id=payload.project_id,
                shot_id=payload.shot_id,
            )
        )
        if normalized.voice_profile_validation is not None:
            self._annotate_voice_profile_outputs(outcome, normalized.metadata)
        if payload.prompt_template_id:
            PromptTemplateService(self.session).record_usage(
                payload.prompt_template_id,
                success=outcome.experiment.status in {"success", "partial_success"},
            )
        return outcome

    def _resolve_text(self, payload: TtsRunInput) -> str:
        if payload.prompt_template_id:
            text = PromptTemplateService(self.session).assemble(payload.prompt_template_id, payload.variables)
        else:
            text = payload.text or ""
        text = text.strip()
        if not text:
            raise VoiceLabValidationError("text is required")
        if len(text) > self.MAX_TEXT_LENGTH:
            raise VoiceLabValidationError("text is too long")
        return text

    def _annotate_voice_profile_outputs(
        self,
        outcome: CapabilityRunOutcome,
        metadata: dict[str, Any],
    ) -> None:
        experiment = outcome.experiment
        experiment.metadata_json = {**(experiment.metadata_json or {}), **metadata}
        experiment.output_json = {
            **(experiment.output_json or {}),
            "metadata": {**((experiment.output_json or {}).get("metadata") or {}), **metadata},
        }
        for ref in experiment.output_asset_refs_json or []:
            asset_id = ref.get("asset_id")
            if not asset_id:
                continue
            asset = self.session.get(Asset, asset_id)
            if asset is None:
                continue
            asset.metadata_json = {**(asset.metadata_json or {}), **metadata}
        self.session.commit()
        self.session.refresh(experiment)
