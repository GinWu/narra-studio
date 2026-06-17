"""Unified model capability orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Protocol

from sqlalchemy.orm import Session

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import CapabilityError, CapabilityRequest, CapabilityResult, RuntimeFileRef
from backend.app.db.models import Experiment, InvocationLog, Model, Provider
from backend.app.services.credential_resolver import CredentialResolutionError, CredentialResolver
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.security_service import SanitizerService
from backend.app.utils.ids import new_id


@dataclass(frozen=True)
class CapabilityRunCommand:
    capability_type: str
    input_json: dict[str, Any]
    params_json: dict[str, Any] | None = None
    existing_experiment_id: str | None = None
    model_id: str | None = None
    prompt_template_id: str | None = None
    parent_experiment_id: str | None = None
    project_id: str | None = None
    shot_id: str | None = None
    result_mode: str = "sync"
    runtime_files: dict[str, RuntimeFileRef] | None = None


@dataclass(frozen=True)
class CapabilityRunOutcome:
    experiment: Experiment
    result: CapabilityResult | None


class AssetResultProcessor(Protocol):
    def process_capability_result(self, experiment: Experiment, result: CapabilityResult) -> list[dict[str, Any]]:
        ...


class CostRecorder(Protocol):
    def record_capability_cost(self, experiment: Experiment, result: CapabilityResult) -> None:
        ...


class CapabilityRunService:
    def __init__(
        self,
        session: Session,
        adapter_registry: AdapterRegistry,
        credential_resolver: CredentialResolver | None = None,
        asset_processor: AssetResultProcessor | None = None,
        cost_recorder: CostRecorder | None = None,
        sanitizer: SanitizerService | None = None,
    ) -> None:
        self.session = session
        self.adapter_registry = adapter_registry
        self.credential_resolver = credential_resolver or CredentialResolver()
        self.asset_processor = asset_processor
        self.cost_recorder = cost_recorder
        self.sanitizer = sanitizer or SanitizerService()
        self.model_registry = ModelRegistryService(session)

    def run(self, command: CapabilityRunCommand) -> CapabilityRunOutcome:
        started = perf_counter()
        experiment = self._create_running_experiment(command)
        result: CapabilityResult | None = None
        model: Model | None = None
        provider: Provider | None = None
        adapter_name: str | None = None
        adapter_version: str | None = None

        try:
            model = self._resolve_model(command)
            provider = self._get_provider(model.provider_id)
            self._validate_provider_model(provider, model)
            adapter_name = model.adapter_key or provider.adapter_name or provider.name
            adapter = self.adapter_registry.resolve(adapter_name, command.capability_type)
            adapter_version = getattr(adapter, "version", None)
            experiment.provider_id = provider.id
            experiment.model_id = model.id
            experiment.adapter_name = adapter_name
            experiment.adapter_version = adapter_version
            self.session.commit()

            credential = self.credential_resolver.resolve(provider)
            self._log_phase(experiment, "adapter_start", "running", provider, model, adapter_name)
            request = CapabilityRequest(
                request_id=new_id("req"),
                experiment_id=experiment.id,
                capability_type=command.capability_type,
                provider=provider,
                model=model,
                credential=credential,
                input_json=command.input_json,
                params_json=command.params_json or {},
                runtime_files=command.runtime_files or {},
                timeout_seconds=provider.timeout_seconds,
            )
            result = self._run_adapter(adapter, request)
            asset_refs = self._process_assets(experiment, result)
            self._finalize_success(experiment, result, asset_refs, started)
            if self.cost_recorder is not None:
                self.cost_recorder.record_capability_cost(experiment, result)
            self._log_phase(experiment, "adapter_finish", result.status, provider, model, adapter_name, result=result)
            self.session.commit()
            self.session.refresh(experiment)
            return CapabilityRunOutcome(experiment=experiment, result=result)
        except CredentialResolutionError as exc:
            error = CapabilityError(exc.code, exc.message)
            self._finalize_error(experiment, error, started, provider, model, adapter_name, adapter_version)
            return CapabilityRunOutcome(experiment=experiment, result=None)
        except CapabilityError as exc:
            self._finalize_error(experiment, exc, started, provider, model, adapter_name, adapter_version)
            return CapabilityRunOutcome(experiment=experiment, result=None)
        except Exception as exc:
            error = CapabilityError("adapter_error", "Adapter execution failed.")
            self._finalize_error(experiment, error, started, provider, model, adapter_name, adapter_version)
            return CapabilityRunOutcome(experiment=experiment, result=None)

    def _create_running_experiment(self, command: CapabilityRunCommand) -> Experiment:
        if command.existing_experiment_id:
            experiment = self.session.get(Experiment, command.existing_experiment_id)
            if experiment is None or experiment.deleted_at is not None:
                raise CapabilityError("experiment_not_found", "Experiment not found.")
            experiment.status = "running"
            experiment.result_mode = command.result_mode
            experiment.started_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(experiment)
            return experiment
        experiment = Experiment(
            id=new_id("exp"),
            started_at=datetime.now(timezone.utc),
            prompt_template_id=command.prompt_template_id,
            parent_experiment_id=command.parent_experiment_id,
            project_id=command.project_id,
            shot_id=command.shot_id,
            capability_type=command.capability_type,
            status="running",
            result_mode=command.result_mode,
            input_json=command.input_json,
            normalized_params_json=command.params_json or {},
        )
        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def _resolve_model(self, command: CapabilityRunCommand) -> Model:
        if command.model_id:
            return self.model_registry.get_model(command.model_id)
        return self.model_registry.get_default_model(command.capability_type)

    def _get_provider(self, provider_id: str) -> Provider:
        provider = self.session.get(Provider, provider_id)
        if provider is None or provider.deleted_at is not None:
            raise CapabilityError("provider_not_found", "Provider not found.")
        return provider

    def _validate_provider_model(self, provider: Provider, model: Model) -> None:
        if not provider.enabled or provider.status == "disabled":
            raise CapabilityError("provider_disabled", "Provider is disabled.")
        if provider.status == "error":
            raise CapabilityError("provider_error", "Provider is in error status.")
        if not model.enabled or model.status == "disabled":
            raise CapabilityError("model_disabled", "Model is disabled.")
        if model.status != "active":
            raise CapabilityError("model_unavailable", "Model is not active.")

    def _process_assets(self, experiment: Experiment, result: CapabilityResult) -> list[dict[str, Any]]:
        if not result.output_files:
            return []
        if self.asset_processor is None:
            return []
        return self.asset_processor.process_capability_result(experiment, result)

    def _run_adapter(self, adapter: Any, request: CapabilityRequest) -> CapabilityResult:
        try:
            method_by_capability = {
                "tts": "run_tts",
                "stt": "run_stt",
                "voice_clone": "run_voice_clone",
            }
            method_name = method_by_capability.get(request.capability_type)
            if method_name and hasattr(adapter, method_name):
                return getattr(adapter, method_name)(request)
            return adapter.run(request)
        except CapabilityError:
            raise
        except Exception as exc:
            map_error = getattr(adapter, "map_error", None)
            if callable(map_error):
                raise map_error(exc) from exc
            raise

    def _finalize_success(
        self,
        experiment: Experiment,
        result: CapabilityResult,
        asset_refs: list[dict[str, Any]],
        started: float,
    ) -> None:
        experiment.status = result.status if result.status in {
            "success",
            "failed",
            "timeout",
            "cancelled",
            "partial_success",
        } else "failed"
        experiment.result_mode = result.result_mode
        experiment.output_json = {
            "output_text": result.output_text,
            "provider_task_id": result.provider_task_id,
            "metadata": self._sanitize_payload(result.metadata),
        }
        experiment.output_text = result.output_text
        experiment.provider_task_id = result.provider_task_id
        experiment.output_asset_refs_json = asset_refs
        experiment.usage_json = self._sanitize_payload(result.usage)
        experiment.cost_usage_json = self._sanitize_payload(result.cost_usage)
        experiment.raw_response_json = self._sanitize_payload(result.raw_response)
        experiment.error_json = self._sanitize_payload(result.error)
        experiment.metadata_json = self._sanitize_payload(result.metadata)
        experiment.duration_ms = _elapsed_ms(started)
        experiment.finished_at = datetime.now(timezone.utc)

    def _finalize_error(
        self,
        experiment: Experiment,
        error: CapabilityError,
        started: float,
        provider: Provider | None,
        model: Model | None,
        adapter_name: str | None,
        adapter_version: str | None,
    ) -> None:
        experiment.status = "timeout" if error.status == "timeout" else "failed"
        experiment.provider_id = provider.id if provider else experiment.provider_id
        experiment.model_id = model.id if model else experiment.model_id
        experiment.adapter_name = adapter_name
        experiment.adapter_version = adapter_version
        experiment.error_json = self._sanitize_payload(error.to_error_json())
        experiment.duration_ms = _elapsed_ms(started)
        experiment.finished_at = datetime.now(timezone.utc)
        self._log_phase(experiment, "failed", experiment.status, provider, model, adapter_name, error=error.to_error_json())
        self.session.commit()
        self.session.refresh(experiment)

    def _log_phase(
        self,
        experiment: Experiment,
        phase: str,
        status: str,
        provider: Provider | None,
        model: Model | None,
        adapter_name: str | None,
        result: CapabilityResult | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        log = InvocationLog(
            id=new_id("ilog"),
            experiment_id=experiment.id,
            provider_id=provider.id if provider else None,
            model_id=model.id if model else None,
            capability_type=experiment.capability_type,
            status=status,
            request_summary_json={"phase": phase, "adapter_name": adapter_name},
            response_summary_json=self._sanitize_payload(result.metadata if result else None),
            metadata_json={"phase": phase},
            error_json=self._sanitize_payload(error),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        self.session.add(log)

    def _sanitize_payload(self, value: Any) -> Any:
        return self.sanitizer.sanitize(value)


def _elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)
