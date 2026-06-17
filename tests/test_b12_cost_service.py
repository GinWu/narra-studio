from __future__ import annotations

from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.types import CapabilityResult
from backend.app.db.base import Base
from backend.app.services.cost_service import CostService, UsageNormalizer
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.provider_service import ProviderService


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return Session(), engine


def _experiment(session, pricing=None):
    provider_name = f"mock_{uuid4().hex[:8]}"
    provider = ProviderService(session).create_provider(
        {"name": provider_name, "credential_source": "none", "enabled": True, "status": "active", "adapter_name": "mock"}
    )
    model = ModelRegistryService(session).create_model(
        {
            "provider_id": provider.id,
            "name": "mock-tts",
            "capability_type": "tts",
            "adapter_key": "mock",
            "pricing_json": pricing,
        }
    )
    return ExperimentService(session).create_running(
        capability_type="tts",
        input_json={"text": "hello"},
        provider_id=provider.id,
        model_id=model.id,
    )


def test_usage_normalizer_prefers_cost_usage_then_usage():
    normalized = UsageNormalizer().normalize(
        CapabilityResult(status="success", usage={"characters": 10}, cost_usage={"input_units": 3})
    )
    assert normalized["input_units"] == 3


def test_cost_record_unknown_cost_is_not_zero_and_aggregates_unknown_count():
    session, engine = _session()
    try:
        exp = _experiment(session)
        service = CostService(session)
        record = service.record_capability_cost(exp, CapabilityResult(status="success", usage={"characters": 5}))
        summary = service.summarize()

        assert record.estimated_cost is None
        assert summary["unknown_cost_count"] == 1
        assert summary["by_currency"] == []
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_cost_summary_groups_different_currencies():
    session, engine = _session()
    try:
        usd = _experiment(session)
        eur = _experiment(session)
        service = CostService(session)
        service.record_capability_cost(
            usd,
            CapabilityResult(status="success", cost_usage={"estimated_cost": "1.25", "currency": "USD"}),
        )
        service.record_capability_cost(
            eur,
            CapabilityResult(status="success", cost_usage={"estimated_cost": "2.50", "currency": "EUR"}),
        )
        summary = service.summarize()

        by_currency = {item["currency"]: item["estimated_cost_total"] for item in summary["by_currency"]}
        assert by_currency == {"USD": "1.25000000", "EUR": "2.50000000"}
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_cost_service_can_estimate_from_pricing_snapshot():
    session, engine = _session()
    try:
        exp = _experiment(session, pricing={"input_unit_cost": "0.01", "currency": "USD"})
        record = CostService(session).record_capability_cost(
            exp,
            CapabilityResult(status="success", usage={"characters": 10}),
        )
        assert str(record.estimated_cost) == "0.10000000"
        assert record.currency == "USD"
    finally:
        session.close()
        Base.metadata.drop_all(engine)
