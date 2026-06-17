"""Evaluation facts and compare aggregation."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Asset, Evaluation, Experiment, PromptTemplate
from backend.app.services.experiment_service import ExperimentService
from backend.app.utils.ids import new_id


class EvaluationValidationError(ValueError):
    pass


class EvaluationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_evaluation(
        self,
        *,
        target_type: str,
        target_id: str,
        dimension: str,
        score: float | None = None,
        label: str | None = None,
        comment: str | None = None,
        evaluator_id: str = "local",
        compare_group_id: str | None = None,
        is_best: bool = False,
        is_failed_case: bool = False,
        metadata_json: dict[str, Any] | None = None,
    ) -> Evaluation:
        self._validate_target(target_type, target_id)
        metadata = dict(metadata_json or {})
        if compare_group_id:
            metadata["compare_group_id"] = compare_group_id
        existing = self._find_active(target_type, target_id, dimension, evaluator_id, compare_group_id)
        if existing is None:
            existing = Evaluation(
                id=new_id("eval"),
                target_type=target_type,
                target_id=target_id,
                dimension=dimension,
                evaluator_id=evaluator_id,
                is_active=True,
            )
            self._bind_target(existing, target_type, target_id)
            self.session.add(existing)
        existing.score = score
        existing.label = label
        existing.comment = comment
        existing.is_best = is_best
        existing.is_failed_case = is_failed_case
        existing.metadata_json = metadata or None
        if is_best and compare_group_id:
            self._clear_compare_group_best(compare_group_id, except_id=existing.id)
        self.session.commit()
        self.session.refresh(existing)
        if target_type == "asset":
            self.refresh_asset_rating(target_id)
        return existing

    def list_evaluations(
        self,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        compare_group_id: str | None = None,
        is_active: bool = True,
    ) -> list[Evaluation]:
        stmt = select(Evaluation).where(Evaluation.deleted_at.is_(None)).where(Evaluation.is_active.is_(is_active))
        if target_type:
            stmt = stmt.where(Evaluation.target_type == target_type)
        if target_id:
            stmt = stmt.where(Evaluation.target_id == target_id)
        evaluations = list(self.session.scalars(stmt.order_by(Evaluation.created_at.desc())).all())
        if compare_group_id:
            evaluations = [item for item in evaluations if (item.metadata_json or {}).get("compare_group_id") == compare_group_id]
        return evaluations

    def mark_experiment_best(self, experiment_id: str) -> Experiment:
        return ExperimentService(self.session).mark_best(experiment_id, True)

    def refresh_asset_rating(self, asset_id: str) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise KeyError("asset_not_found")
        evaluations = self.list_evaluations(target_type="asset", target_id=asset_id)
        usability = [item.score for item in evaluations if item.dimension == "可用性" and item.score is not None]
        all_scores = [item.score for item in evaluations if item.score is not None]
        if usability:
            asset.rating = usability[-1]
        elif all_scores:
            asset.rating = sum(all_scores) / len(all_scores)
        else:
            asset.rating = None
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def save_compare_conclusion(
        self,
        *,
        target_ids: list[str],
        comment: str,
        compare_group_id: str | None = None,
        evaluator_id: str = "local",
    ) -> Evaluation:
        group_id = compare_group_id or stable_compare_group_id(target_ids)
        return self.upsert_evaluation(
            target_type="compare_group",
            target_id=group_id,
            dimension="conclusion",
            comment=comment,
            evaluator_id=evaluator_id,
            compare_group_id=group_id,
            metadata_json={"target_ids": target_ids},
        )

    def _find_active(
        self,
        target_type: str,
        target_id: str,
        dimension: str,
        evaluator_id: str,
        compare_group_id: str | None,
    ) -> Evaluation | None:
        stmt = (
            select(Evaluation)
            .where(Evaluation.deleted_at.is_(None))
            .where(Evaluation.is_active.is_(True))
            .where(Evaluation.target_type == target_type)
            .where(Evaluation.target_id == target_id)
            .where(Evaluation.dimension == dimension)
            .where(Evaluation.evaluator_id == evaluator_id)
        )
        for evaluation in self.session.scalars(stmt).all():
            if (evaluation.metadata_json or {}).get("compare_group_id") == compare_group_id:
                return evaluation
        return None

    def _validate_target(self, target_type: str, target_id: str) -> None:
        model_by_type = {
            "experiment": Experiment,
            "asset": Asset,
            "prompt_template": PromptTemplate,
        }
        if target_type == "compare_group":
            return
        model = model_by_type.get(target_type)
        if model is None:
            raise EvaluationValidationError("unsupported target_type")
        target = self.session.get(model, target_id)
        if target is None or getattr(target, "deleted_at", None) is not None:
            raise KeyError(f"{target_type}_not_found")

    def _bind_target(self, evaluation: Evaluation, target_type: str, target_id: str) -> None:
        if target_type == "experiment":
            evaluation.experiment_id = target_id
        elif target_type == "asset":
            evaluation.asset_id = target_id
        elif target_type == "prompt_template":
            evaluation.prompt_template_id = target_id

    def _clear_compare_group_best(self, compare_group_id: str, except_id: str) -> None:
        for evaluation in self.list_evaluations(compare_group_id=compare_group_id):
            if evaluation.id != except_id:
                evaluation.is_best = False


class CompareService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_compare_items(self, experiment_ids: list[str]) -> list[dict[str, Any]]:
        evaluation_service = EvaluationService(self.session)
        items: list[dict[str, Any]] = []
        for experiment_id in experiment_ids:
            experiment = self.session.get(Experiment, experiment_id)
            if experiment is None or experiment.deleted_at is not None:
                continue
            evaluations = evaluation_service.list_evaluations(target_type="experiment", target_id=experiment_id)
            items.append(
                {
                    "experiment_id": experiment.id,
                    "status": experiment.status,
                    "capability_type": experiment.capability_type,
                    "is_best": experiment.is_best,
                    "evaluations": [
                        {
                            "id": evaluation.id,
                            "dimension": evaluation.dimension,
                            "score": evaluation.score,
                            "is_best": evaluation.is_best,
                            "metadata_json": evaluation.metadata_json,
                        }
                        for evaluation in evaluations
                    ],
                }
            )
        return items


def stable_compare_group_id(target_ids: list[str]) -> str:
    joined = "|".join(sorted(target_ids))
    return f"cmp_{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:16]}"
