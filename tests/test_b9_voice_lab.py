from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import MockAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import Asset
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.prompt_template_service import PromptTemplateService
from backend.app.services.provider_service import ProviderService
from backend.app.services.voice_lab_service import TtsRunInput, VoiceLabService, VoiceLabValidationError


@pytest.fixture()
def db_session(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("AIWM_WORKSPACE_ROOT", str(tmp_path))
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


def _voice_service(db_session):
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
    return VoiceLabService(db_session, registry)


def test_voice_lab_mock_tts_creates_experiment_and_asset(db_session, tmp_path):
    outcome = _voice_service(db_session).run_tts(TtsRunInput(text="Hello", voice="alloy"))

    assert outcome.experiment.status == "success"
    assert outcome.experiment.capability_type == "tts"
    assert outcome.experiment.output_asset_refs_json
    asset = db_session.get(Asset, outcome.experiment.output_asset_refs_json[0]["asset_id"])
    assert asset is not None
    assert asset.asset_type == "audio"
    assert asset.relative_path.startswith("assets/audio/")
    assert (tmp_path / asset.relative_path).is_file()


def test_voice_lab_uses_prompt_template_specific_version(db_session):
    prompt = PromptTemplateService(db_session).create_template(
        {
            "name": "voice",
            "capability_type": "tts",
            "content": "Say {{text}}",
            "default_values_json": {"text": "hello"},
        }
    )
    outcome = _voice_service(db_session).run_tts(TtsRunInput(prompt_template_id=prompt.id, variables={"text": "hi"}))
    db_session.refresh(prompt)

    assert outcome.experiment.prompt_template_id == prompt.id
    assert outcome.experiment.input_json == {"text": "Say hi"}
    assert prompt.usage_count == 1
    assert prompt.success_count == 1


def test_voice_lab_validates_text_and_speed(db_session):
    service = _voice_service(db_session)
    with pytest.raises(VoiceLabValidationError):
        service.run_tts(TtsRunInput(text=""))
    with pytest.raises(VoiceLabValidationError):
        service.run_tts(TtsRunInput(text="hello", speed=3.0))
