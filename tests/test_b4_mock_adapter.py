from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import MockAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.db.base import Base
from backend.app.services.capability_run_service import CapabilityRunCommand, CapabilityRunService
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


def _service(db_session):
    provider = ProviderService(db_session).create_provider(
        {
            "name": "mock",
            "provider_type": "mock",
            "credential_source": "none",
            "enabled": True,
            "status": "active",
            "adapter_name": "mock",
        }
    )
    ModelRegistryService(db_session).seed_mock_models(provider.id)
    registry = AdapterRegistry()
    registry.register(MockAdapter())
    return CapabilityRunService(db_session, registry)


@pytest.mark.parametrize(
    ("capability_type", "input_json", "expected_type"),
    [
        ("tts", {"text": "hello"}, "audio"),
        ("image_generation", {"prompt": "a red dot"}, "image"),
        ("video_generation", {"prompt": "a short clip"}, "video"),
    ],
)
def test_mock_adapter_success_outputs_temp_files(db_session, capability_type, input_json, expected_type):
    outcome = _service(db_session).run(
        CapabilityRunCommand(capability_type=capability_type, input_json=input_json)
    )

    assert outcome.experiment.status == "success"
    assert outcome.result is not None
    output = outcome.result.output_files[0]
    assert output.file_type == expected_type
    assert output.temp_path is not None
    assert Path(output.temp_path).is_file()


@pytest.mark.parametrize("mock_status", ["failed", "timeout", "partial_success"])
def test_mock_adapter_status_scenarios(db_session, mock_status):
    outcome = _service(db_session).run(
        CapabilityRunCommand(
            capability_type="tts",
            input_json={"text": "hello"},
            params_json={"mock_status": mock_status},
        )
    )

    assert outcome.experiment.status == mock_status
    if mock_status == "partial_success":
        assert outcome.result is not None
        assert outcome.result.output_files
    else:
        assert outcome.experiment.error_json["error_type"].startswith("mock_")


def test_mock_adapter_can_return_source_url_without_final_asset_path(db_session):
    outcome = _service(db_session).run(
        CapabilityRunCommand(
            capability_type="image_generation",
            input_json={"prompt": "a source url"},
            params_json={"mock_source_url": True},
        )
    )

    assert outcome.experiment.status == "success"
    assert outcome.result is not None
    output = outcome.result.output_files[0]
    assert output.temp_path is None
    assert output.source_url is not None
    assert output.source_url.startswith("https://mock.local/")
