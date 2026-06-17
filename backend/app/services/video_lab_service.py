"""Video Lab async workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.services.asset_service import AssetService
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunOutcome, CapabilityRunService
from backend.app.services.cost_service import CostService
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.prompt_template_service import PromptTemplateService
from backend.app.services.task_service import TaskService


class VideoLabValidationError(ValueError):
    pass


class VideoTaskQueueError(RuntimeError):
    pass


@dataclass(frozen=True)
class VideoGenerationInput:
    prompt: str | None = None
    negative_prompt: str | None = None
    prompt_template_id: str | None = None
    variables: dict[str, Any] | None = None
    model_id: str | None = None
    duration_seconds: int | None = None
    aspect_ratio: str | None = None
    params_json: dict[str, Any] | None = None
    project_id: str | None = None
    shot_id: str | None = None


@dataclass(frozen=True)
class VideoTaskCreated:
    task_id: str
    experiment_id: str
    status: str


class VideoLabService:
    MAX_PROMPT_LENGTH = 8000

    def __init__(self, session: Session, adapter_registry: AdapterRegistry) -> None:
        self.session = session
        self.adapter_registry = adapter_registry

    def create_video_task(self, payload: VideoGenerationInput, *, run_immediately: bool = False) -> VideoTaskCreated:
        prompt = self._resolve_prompt(payload)
        params = dict(payload.params_json or {})
        if payload.duration_seconds is not None:
            if not 1 <= payload.duration_seconds <= 60:
                raise VideoLabValidationError("duration_seconds must be between 1 and 60")
            params["duration_seconds"] = payload.duration_seconds
        if payload.aspect_ratio:
            params["aspect_ratio"] = payload.aspect_ratio

        input_json = {"prompt": prompt}
        if payload.negative_prompt:
            input_json["negative_prompt"] = payload.negative_prompt

        experiment = ExperimentService(self.session).create_running(
            capability_type="video_generation",
            input_json=input_json,
            normalized_params_json=params,
            result_mode="async_task",
            prompt_template_id=payload.prompt_template_id,
            project_id=payload.project_id,
            shot_id=payload.shot_id,
        )
        task_service = TaskService(self.session)
        task = task_service.create_task(
            task_type="video_generation",
            experiment_id=experiment.id,
            model_id=payload.model_id,
            request_json={
                "capability_type": "video_generation",
                "input_json": input_json,
                "params_json": params,
                "model_id": payload.model_id,
                "prompt_template_id": payload.prompt_template_id,
            },
            queue_name="video",
            timeout_seconds=600,
        )
        if run_immediately:
            task = task_service.mark_queued(task.id, celery_task_id="inline")
            self.run_video_task(task.id)
            task = task_service.get_task(task.id)
        else:
            try:
                celery_task_id = enqueue_video_generation(task.id)
            except Exception as exc:
                task = task_service.mark_failed(
                    task.id,
                    error_json={
                        "error_type": "queue_submit_failed",
                        "message": "Video task could not be submitted to the worker queue.",
                    },
                )
            else:
                task = task_service.get_task(task.id)
                if task.status == "pending":
                    task = task_service.mark_queued(task.id, celery_task_id=celery_task_id)
                else:
                    task.celery_task_id = celery_task_id
                    self.session.commit()
                    self.session.refresh(task)
        return VideoTaskCreated(task_id=task.id, experiment_id=experiment.id, status=task.status)

    def run_video_task(self, task_id: str) -> CapabilityRunOutcome:
        task_service = TaskService(self.session)
        task = task_service.mark_running(task_id)
        request = task.request_json or {}
        outcome = CapabilityRunService(
            self.session,
            self.adapter_registry,
            asset_processor=AssetService(self.session),
            cost_recorder=CostService(self.session),
        ).run(
            CapabilityRunCommand(
                capability_type="video_generation",
                input_json=request["input_json"],
                params_json=request.get("params_json"),
                existing_experiment_id=task.experiment_id,
                model_id=request.get("model_id"),
                prompt_template_id=request.get("prompt_template_id"),
                result_mode="async_task",
            )
        )
        if outcome.experiment.status in {"success", "partial_success"}:
            task_service.mark_succeeded(task_id, result_json={"experiment_id": outcome.experiment.id})
        elif outcome.experiment.status == "timeout":
            task_service.mark_timeout(task_id, error_json=outcome.experiment.error_json)
        elif outcome.experiment.status == "cancelled":
            task_service.mark_cancelled(task_id, error_json=outcome.experiment.error_json)
        else:
            task_service.mark_failed(task_id, error_json=outcome.experiment.error_json)
        if request.get("prompt_template_id"):
            PromptTemplateService(self.session).record_usage(
                request["prompt_template_id"],
                success=outcome.experiment.status in {"success", "partial_success"},
            )
        return outcome

    def _resolve_prompt(self, payload: VideoGenerationInput) -> str:
        if payload.prompt_template_id:
            prompt = PromptTemplateService(self.session).assemble(payload.prompt_template_id, payload.variables)
        else:
            prompt = payload.prompt or ""
        prompt = prompt.strip()
        if not prompt:
            raise VideoLabValidationError("prompt is required")
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            raise VideoLabValidationError("prompt is too long")
        return prompt


def enqueue_video_generation(task_id: str) -> str:
    from backend.app.tasks.video_tasks import enqueue_video_generation as enqueue

    return enqueue(task_id)
