from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import AdapterHealthResult, CapabilityError, CapabilityRequest, CapabilityResult
from backend.app.db.base import Base
from backend.app.db.models import Experiment, InvocationLog
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunService
from backend.app.services.credential_resolver import ResolvedCredential
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.provider_service import ProviderService


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with Session() as session:
        yield session
    Base.metadata.drop_all(engine)


class FakeAdapter:
    name = "fake"
    version = "1.0"
    supported_capabilities = ["tts", "image_generation"]

    def __init__(self, session, status: str = "success") -> None:
        self.session = session
        self.status = status
        self.seen_running = False
        self.seen_credential_value = None

    def supports(self, capability_type: str) -> bool:
        return capability_type in self.supported_capabilities

    def health_check(self, provider, credential: ResolvedCredential) -> AdapterHealthResult:
        return AdapterHealthResult(ok=True, message="ok")

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        experiment = self.session.get(Experiment, request.experiment_id)
        self.seen_running = experiment is not None and experiment.status == "running"
        self.seen_credential_value = request.credential.value
        return CapabilityResult(
            status=self.status,
            result_mode="sync",
            output_text="ok",
            usage={"characters": 2},
            cost_usage={"input_units": 2, "api_key": "should-not-persist"},
            raw_response={"authorization": "Bearer secret", "id": "provider-result"},
            metadata={"phase": "done"},
        )

    def map_error(self, exc: Exception) -> CapabilityError:
        return CapabilityError("fake_error", "fake error")


def _provider_model(db_session, *, credential_source="none", credential_ref=None, enabled=True):
    provider = ProviderService(db_session).create_provider(
        {
            "name": "fake",
            "credential_source": credential_source,
            "credential_ref": credential_ref,
            "enabled": enabled,
            "status": "active" if enabled else "disabled",
            "adapter_name": "fake",
        }
    )
    model = ModelRegistryService(db_session).create_model(
        {
            "provider_id": provider.id,
            "name": "fake-tts",
            "capability_type": "tts",
            "adapter_key": "fake",
            "is_default": True,
        }
    )
    return provider, model


def test_capability_run_creates_running_experiment_before_adapter_and_succeeds(db_session):
    _provider_model(db_session)
    adapter = FakeAdapter(db_session)
    registry = AdapterRegistry()
    registry.register(adapter)

    outcome = CapabilityRunService(db_session, registry).run(
        CapabilityRunCommand(capability_type="tts", input_json={"text": "hi"})
    )

    assert adapter.seen_running is True
    assert outcome.experiment.status == "success"
    assert outcome.experiment.adapter_name == "fake"
    assert outcome.experiment.output_json["output_text"] == "ok"
    assert outcome.experiment.raw_response_json["authorization"] == "[REDACTED]"
    assert outcome.experiment.cost_usage_json["api_key"] == "[REDACTED]"

    logs = db_session.scalars(select(InvocationLog).where(InvocationLog.experiment_id == outcome.experiment.id)).all()
    assert {log.metadata_json["phase"] for log in logs} == {"adapter_start", "adapter_finish"}


def test_capability_run_credential_failure_still_creates_failed_experiment(db_session):
    _provider_model(db_session, credential_source="env", credential_ref="AIWM_MISSING_FOR_B3")
    registry = AdapterRegistry()
    registry.register(FakeAdapter(db_session))

    outcome = CapabilityRunService(db_session, registry).run(
        CapabilityRunCommand(capability_type="tts", input_json={"text": "hi"})
    )

    assert outcome.experiment.status == "failed"
    assert outcome.experiment.error_json["error_type"] == "credential_not_found"
    assert outcome.result is None


def test_capability_run_adapter_validation_failure_is_recorded(db_session):
    _provider_model(db_session)
    registry = AdapterRegistry()

    outcome = CapabilityRunService(db_session, registry).run(
        CapabilityRunCommand(capability_type="tts", input_json={"text": "hi"})
    )

    assert outcome.experiment.status == "failed"
    assert outcome.experiment.error_json["error_type"] == "adapter_not_found"
