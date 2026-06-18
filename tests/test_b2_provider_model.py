from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.models import create_model as create_model_route
from backend.app.api.providers import create_provider as create_provider_route
from backend.app.db.base import Base
from backend.app.schemas.model_registry import ModelCreate
from backend.app.schemas.provider import ProviderCreate, ProviderRead
from backend.app.services.credential_resolver import CredentialResolutionError, CredentialResolver
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


def test_credential_resolver_sources(tmp_path: Path, monkeypatch, db_session):
    service = ProviderService(db_session)
    none_provider = service.create_provider({"name": "mock", "credential_source": "none", "enabled": True})
    assert CredentialResolver().resolve(none_provider).value is None

    monkeypatch.setenv("AIWM_TEST_KEY", "secret-value")
    env_provider = service.create_provider(
        {"name": "env_provider", "credential_source": "env", "credential_ref": "AIWM_TEST_KEY"}
    )
    assert CredentialResolver().resolve(env_provider).value == "secret-value"

    secret_file = tmp_path / "secret"
    secret_file.write_text("file-secret\n", encoding="utf-8")
    file_provider = service.create_provider(
        {"name": "file_provider", "credential_source": "file", "credential_file": str(secret_file)}
    )
    assert CredentialResolver().resolve(file_provider).value == "file-secret"


def test_credential_resolver_rejects_missing_and_deferred(db_session):
    service = ProviderService(db_session)
    missing = service.create_provider(
        {"name": "missing", "credential_source": "env", "credential_ref": "AIWM_MISSING_KEY"}
    )
    with pytest.raises(CredentialResolutionError) as missing_exc:
        CredentialResolver().resolve(missing)
    assert missing_exc.value.code == "credential_not_found"

    deferred = service.create_provider({"name": "deferred", "credential_source": "encrypted_local"})
    with pytest.raises(CredentialResolutionError) as deferred_exc:
        CredentialResolver().resolve(deferred)
    assert deferred_exc.value.code == "unsupported_credential_source"


def test_provider_service_masks_and_tests_connection(db_session):
    service = ProviderService(db_session)
    provider = service.create_provider(
        {
            "name": "openai",
            "credential_source": "env",
            "credential_ref": "OPENAI_API_KEY",
            "enabled": True,
        }
    )

    assert provider.masked_credential == "OPEN..._KEY"
    result = service.test_connection(provider.id)
    assert result["ok"] is False
    assert result["code"] == "credential_not_found"
    db_session.refresh(provider)
    assert provider.last_health_error == "credential_not_found"


def test_provider_partial_update_preserves_masked_credential(db_session):
    service = ProviderService(db_session)
    provider = service.create_provider(
        {
            "name": "openai",
            "display_name": "OpenAI",
            "credential_source": "env",
            "credential_ref": "OPENAI_API_KEY",
            "enabled": True,
        }
    )
    assert provider.masked_credential == "OPEN..._KEY"

    updated = service.update_provider(provider.id, {"enabled": False})
    assert updated.enabled is False
    assert updated.masked_credential == "OPEN..._KEY"

    updated = service.update_provider(provider.id, {"display_name": "OpenAI Cloud"})
    assert updated.display_name == "OpenAI Cloud"
    assert updated.masked_credential == "OPEN..._KEY"

    updated = service.update_provider(provider.id, {"credential_ref": "SECONDARY_TOKEN"})
    assert updated.masked_credential == "SECO...OKEN"


def test_model_registry_default_model_is_unique(db_session):
    provider = ProviderService(db_session).create_provider({"name": "mock", "credential_source": "none"})
    registry = ModelRegistryService(db_session)
    first = registry.create_model(
        {
            "provider_id": provider.id,
            "name": "mock-tts-a",
            "capability_type": "tts",
            "adapter_key": "mock",
            "is_default": True,
        }
    )
    second = registry.create_model(
        {
            "provider_id": provider.id,
            "name": "mock-tts-b",
            "capability_type": "tts",
            "adapter_key": "mock",
            "is_default": True,
        }
    )

    db_session.refresh(first)
    assert first.is_default is False
    assert second.is_default is True
    assert registry.get_default_model("tts").id == second.id


def test_provider_and_model_api_do_not_return_credentials(db_session):
    provider = create_provider_route(
        ProviderCreate(
            name="mock",
            credential_source="none",
            enabled=True,
            adapter_name="mock",
        ),
        db_session,
    )
    provider_payload = ProviderRead.model_validate(provider).model_dump()
    assert "credential" not in provider_payload
    assert provider_payload["credential_ref"] is None
    assert provider_payload["masked_credential"] is None

    model = create_model_route(
        ModelCreate(
            provider_id=provider.id,
            name="mock-image",
            capability_type="image_generation",
            adapter_key="mock",
            is_default=True,
        ),
        db_session,
    )
    assert model.provider_id == provider.id
