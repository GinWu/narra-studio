"""Image Lab text-to-image workflow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.services.asset_service import AssetService
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunOutcome, CapabilityRunService
from backend.app.services.cost_service import CostService
from backend.app.services.prompt_template_service import PromptTemplateService


class ImageLabValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ImageGenerationInput:
    prompt: str | None = None
    negative_prompt: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    size: str | None = None
    aspect_ratio: str | None = None
    n: int = 1
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None


class ImageParamNormalizer:
    size_pattern = re.compile(r"^\d{2,5}x\d{2,5}$")
    ratio_pattern = re.compile(r"^\d{1,3}:\d{1,3}$")

    def normalize(self, payload: ImageGenerationInput) -> dict[str, Any]:
        params = dict(payload.params_json or {})
        if payload.size:
            if not self.size_pattern.match(payload.size):
                raise ImageLabValidationError("size must look like 1024x1024")
            params["size"] = payload.size
        if payload.aspect_ratio:
            if not self.ratio_pattern.match(payload.aspect_ratio):
                raise ImageLabValidationError("aspect_ratio must look like 1:1")
            params["aspect_ratio"] = payload.aspect_ratio
        if not 1 <= payload.n <= 4:
            raise ImageLabValidationError("n must be between 1 and 4")
        params["n"] = payload.n
        return params


class ImageLabService:
    MAX_PROMPT_LENGTH = 8000

    def __init__(self, session: Session, adapter_registry: AdapterRegistry) -> None:
        self.session = session
        self.adapter_registry = adapter_registry

    def run_image_generation(self, payload: ImageGenerationInput) -> CapabilityRunOutcome:
        final_prompt = self._resolve_prompt(payload)
        params = ImageParamNormalizer().normalize(payload)
        input_json = {"prompt": final_prompt}
        if payload.negative_prompt:
            input_json["negative_prompt"] = payload.negative_prompt

        outcome = CapabilityRunService(
            self.session,
            self.adapter_registry,
            asset_processor=AssetService(self.session),
            cost_recorder=CostService(self.session),
        ).run(
            CapabilityRunCommand(
                capability_type="image_generation",
                input_json=input_json,
                params_json=params,
                model_id=payload.model_id,
                prompt_template_id=payload.prompt_template_id,
                project_id=payload.project_id,
                shot_id=payload.shot_id,
            )
        )
        if payload.prompt_template_id:
            PromptTemplateService(self.session).record_usage(
                payload.prompt_template_id,
                success=outcome.experiment.status in {"success", "partial_success"},
            )
        return outcome

    def _resolve_prompt(self, payload: ImageGenerationInput) -> str:
        if payload.prompt_template_id:
            prompt = PromptTemplateService(self.session).assemble(payload.prompt_template_id, payload.variables)
        else:
            prompt = payload.prompt or ""
        prompt = prompt.strip()
        if not prompt:
            raise ImageLabValidationError("prompt is required")
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            raise ImageLabValidationError("prompt is too long")
        return prompt
