"""Experiment fact management and query APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.enums import EXPERIMENT_STATUSES, RESULT_MODES
from backend.app.db.models import Experiment
from backend.app.utils.ids import new_id

if TYPE_CHECKING:
    from backend.app.services.capability_run_service import CapabilityRunCommand


class ExperimentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_running(
        self,
        *,
        capability_type: str,
        input_json: dict[str, Any],
        normalized_params_json: dict[str, Any] | None = None,
        result_mode: str = "sync",
        provider_id: str | None = None,
        model_id: str | None = None,
        prompt_template_id: str | None = None,
        parent_experiment_id: str | None = None,
        project_id: str | None = None,
        shot_id: str | None = None,
    ) -> Experiment:
        if result_mode not in RESULT_MODES:
            raise ValueError("invalid_result_mode")
        experiment = Experiment(
            id=new_id("exp"),
            provider_id=provider_id,
            model_id=model_id,
            prompt_template_id=prompt_template_id,
            parent_experiment_id=parent_experiment_id,
            project_id=project_id,
            shot_id=shot_id,
            capability_type=capability_type,
            status="running" if result_mode == "sync" else "pending",
            result_mode=result_mode,
            input_json=input_json,
            normalized_params_json=normalized_params_json or {},
            started_at=datetime.now(timezone.utc) if result_mode == "sync" else None,
        )
        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment:
        experiment = self.session.get(Experiment, experiment_id)
        if experiment is None or experiment.deleted_at is not None:
            raise KeyError("experiment_not_found")
        return experiment

    def list_experiments(
        self,
        *,
        capability_type: str | None = None,
        status: str | None = None,
        result_mode: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        project_id: str | None = None,
        shot_id: str | None = None,
        is_best: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Experiment]:
        stmt = select(Experiment).where(Experiment.deleted_at.is_(None)).order_by(Experiment.created_at.desc())
        if capability_type:
            stmt = stmt.where(Experiment.capability_type == capability_type)
        if status:
            stmt = stmt.where(Experiment.status == status)
        if result_mode:
            stmt = stmt.where(Experiment.result_mode == result_mode)
        if provider_id:
            stmt = stmt.where(Experiment.provider_id == provider_id)
        if model_id:
            stmt = stmt.where(Experiment.model_id == model_id)
        if project_id:
            stmt = stmt.where(Experiment.project_id == project_id)
        if shot_id:
            stmt = stmt.where(Experiment.shot_id == shot_id)
        if is_best is not None:
            stmt = stmt.where(Experiment.is_best.is_(is_best))
        return list(self.session.scalars(stmt.limit(limit).offset(offset)).all())

    def update_status(
        self,
        experiment_id: str,
        *,
        status: str,
        output_asset_refs_json: list[dict[str, Any]] | None = None,
        output_json: dict[str, Any] | None = None,
        error_json: dict[str, Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Experiment:
        if status not in EXPERIMENT_STATUSES:
            raise ValueError("invalid_experiment_status")
        experiment = self.get_experiment(experiment_id)
        experiment.status = status
        if output_asset_refs_json is not None:
            experiment.output_asset_refs_json = output_asset_refs_json
        if output_json is not None:
            experiment.output_json = output_json
        if error_json is not None:
            experiment.error_json = error_json
        if metadata_json is not None:
            experiment.metadata_json = metadata_json
        if status in {"success", "failed", "timeout", "cancelled", "partial_success"}:
            experiment.finished_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def update_output_asset_refs(self, experiment_id: str, asset_refs: list[dict[str, Any]]) -> Experiment:
        experiment = self.get_experiment(experiment_id)
        experiment.output_asset_refs_json = asset_refs
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def patch_experiment(self, experiment_id: str, data: dict[str, Any]) -> Experiment:
        allowed = {"title", "notes", "is_best", "is_failed_case", "failed_reason", "metadata_json"}
        experiment = self.get_experiment(experiment_id)
        for key, value in data.items():
            if key in allowed:
                setattr(experiment, key, value)
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def mark_best(self, experiment_id: str, is_best: bool = True) -> Experiment:
        experiment = self.get_experiment(experiment_id)
        experiment.is_best = is_best
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def mark_failed_case(self, experiment_id: str, failed_reason: str | None = None) -> Experiment:
        experiment = self.get_experiment(experiment_id)
        experiment.is_failed_case = True
        experiment.failed_reason = failed_reason
        self.session.commit()
        self.session.refresh(experiment)
        return experiment

    def build_rerun_command(self, experiment_id: str) -> CapabilityRunCommand:
        from backend.app.services.capability_run_service import CapabilityRunCommand
        experiment = self.get_experiment(experiment_id)
        return CapabilityRunCommand(
            capability_type=experiment.capability_type,
            input_json=experiment.input_json,
            params_json=experiment.normalized_params_json,
            model_id=experiment.model_id,
            prompt_template_id=experiment.prompt_template_id,
            parent_experiment_id=experiment.id,
            project_id=experiment.project_id,
            shot_id=experiment.shot_id,
            result_mode="sync",
        )
