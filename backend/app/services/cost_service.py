"""Cost estimation records and invocation log read APIs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.capabilities.types import CapabilityResult
from backend.app.db.models import CostRecord, Experiment, InvocationLog
from backend.app.utils.ids import new_id


class UsageNormalizer:
    def normalize(self, result: CapabilityResult) -> dict[str, Any]:
        usage = result.usage or {}
        cost_usage = result.cost_usage or {}
        normalized = {
            "input_units": cost_usage.get(
                "input_units",
                usage.get("characters", usage.get("seconds", usage.get("minutes", usage.get("requests")))),
            ),
            "output_units": cost_usage.get(
                "output_units",
                usage.get("images", usage.get("videos", usage.get("outputs", usage.get("requests")))),
            ),
            "unit_type": cost_usage.get("unit_type", usage.get("unit_type")),
        }
        return {key: value for key, value in normalized.items() if value is not None}


class CostService:
    def __init__(self, session: Session, usage_normalizer: UsageNormalizer | None = None) -> None:
        self.session = session
        self.usage_normalizer = usage_normalizer or UsageNormalizer()

    def record_capability_cost(self, experiment: Experiment, result: CapabilityResult) -> CostRecord:
        normalized_usage = self.usage_normalizer.normalize(result)
        estimated_cost = self._estimated_cost(experiment, result, normalized_usage)
        currency = self._currency(experiment, result)
        record = CostRecord(
            id=new_id("cost"),
            experiment_id=experiment.id,
            provider_id=experiment.provider_id,
            model_id=experiment.model_id,
            capability_type=experiment.capability_type,
            usage_json=result.usage,
            normalized_usage_json=normalized_usage,
            pricing_snapshot_json=self._pricing_snapshot(experiment),
            estimated_cost=estimated_cost,
            currency=currency,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_for_experiment(self, experiment_id: str) -> list[CostRecord]:
        stmt = select(CostRecord).where(CostRecord.experiment_id == experiment_id).order_by(CostRecord.created_at)
        return list(self.session.scalars(stmt).all())

    def summarize(
        self,
        *,
        provider_id: str | None = None,
        model_id: str | None = None,
        capability_type: str | None = None,
    ) -> dict[str, Any]:
        stmt = select(CostRecord)
        if provider_id:
            stmt = stmt.where(CostRecord.provider_id == provider_id)
        if model_id:
            stmt = stmt.where(CostRecord.model_id == model_id)
        if capability_type:
            stmt = stmt.where(CostRecord.capability_type == capability_type)
        records = list(self.session.scalars(stmt).all())
        by_currency: dict[str, dict[str, Any]] = {}
        unknown_cost_count = 0
        for record in records:
            if record.estimated_cost is None:
                unknown_cost_count += 1
                continue
            currency = record.currency or "UNKNOWN"
            bucket = by_currency.setdefault(currency, {"currency": currency, "estimated_cost_total": Decimal("0"), "count": 0})
            bucket["estimated_cost_total"] += record.estimated_cost
            bucket["count"] += 1
        return {
            "record_count": len(records),
            "unknown_cost_count": unknown_cost_count,
            "by_currency": [
                {
                    "currency": item["currency"],
                    "estimated_cost_total": str(item["estimated_cost_total"]),
                    "count": item["count"],
                }
                for item in by_currency.values()
            ],
        }

    def _estimated_cost(
        self,
        experiment: Experiment,
        result: CapabilityResult,
        normalized_usage: dict[str, Any],
    ) -> Decimal | None:
        cost_usage = result.cost_usage or {}
        if cost_usage.get("estimated_cost") is not None:
            return Decimal(str(cost_usage["estimated_cost"]))
        pricing = self._pricing_snapshot(experiment)
        if not pricing:
            return None
        input_price = pricing.get("input_unit_cost")
        output_price = pricing.get("output_unit_cost")
        total = Decimal("0")
        used = False
        if input_price is not None and normalized_usage.get("input_units") is not None:
            total += Decimal(str(input_price)) * Decimal(str(normalized_usage["input_units"]))
            used = True
        if output_price is not None and normalized_usage.get("output_units") is not None:
            total += Decimal(str(output_price)) * Decimal(str(normalized_usage["output_units"]))
            used = True
        return total if used else None

    def _currency(self, experiment: Experiment, result: CapabilityResult) -> str | None:
        cost_usage = result.cost_usage or {}
        if cost_usage.get("currency"):
            return str(cost_usage["currency"])
        pricing = self._pricing_snapshot(experiment)
        return pricing.get("currency") if pricing else None

    def _pricing_snapshot(self, experiment: Experiment) -> dict[str, Any] | None:
        if not experiment.model_id:
            return None
        from backend.app.db.models import Model

        model = self.session.get(Model, experiment.model_id)
        return model.pricing_json if model else None


class InvocationLogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_logs(
        self,
        *,
        experiment_id: str | None = None,
        task_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        limit: int = 100,
    ) -> list[InvocationLog]:
        stmt = select(InvocationLog).order_by(InvocationLog.created_at.desc()).limit(limit)
        if experiment_id:
            stmt = stmt.where(InvocationLog.experiment_id == experiment_id)
        if task_id:
            stmt = stmt.where(InvocationLog.task_id == task_id)
        if provider_id:
            stmt = stmt.where(InvocationLog.provider_id == provider_id)
        if model_id:
            stmt = stmt.where(InvocationLog.model_id == model_id)
        return list(self.session.scalars(stmt).all())
