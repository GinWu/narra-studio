from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import MockAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.db.base import Base
from backend.app.db.models import Asset
from backend.app.services.image_lab_service import ImageGenerationInput, ImageLabService, ImageLabValidationError
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.prompt_template_service import PromptTemplateService
from backend.app.services.provider_service import ProviderService


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


def _image_service(db_session):
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
    return ImageLabService(db_session, registry)


def test_image_lab_mock_generation_creates_image_asset(db_session, tmp_path):
    outcome = _image_service(db_session).run_image_generation(
        ImageGenerationInput(prompt="a red dot", size="512x512", aspect_ratio="1:1", n=1)
    )

    assert outcome.experiment.status == "success"
    assert outcome.experiment.capability_type == "image_generation"
    asset = db_session.get(Asset, outcome.experiment.output_asset_refs_json[0]["asset_id"])
    assert asset is not None
    assert asset.asset_type == "image"
    assert asset.relative_path.startswith("assets/image/")
    assert (tmp_path / asset.relative_path).is_file()


def test_image_lab_uses_prompt_template_version_and_negative_prompt(db_session):
    prompt = PromptTemplateService(db_session).create_template(
        {
            "name": "image",
            "capability_type": "image_generation",
            "content": "Draw {{subject}}",
        }
    )

    outcome = _image_service(db_session).run_image_generation(
        ImageGenerationInput(
            prompt_template_id=prompt.id,
            variables={"subject": "a tree"},
            negative_prompt="blur",
        )
    )
    db_session.refresh(prompt)

    assert outcome.experiment.prompt_template_id == prompt.id
    assert outcome.experiment.input_json == {"prompt": "Draw a tree", "negative_prompt": "blur"}
    assert prompt.usage_count == 1


def test_image_lab_param_validation(db_session):
    service = _image_service(db_session)
    with pytest.raises(ImageLabValidationError):
        service.run_image_generation(ImageGenerationInput(prompt="x", size="large"))
    with pytest.raises(ImageLabValidationError):
        service.run_image_generation(ImageGenerationInput(prompt="x", n=5))
    with pytest.raises(ImageLabValidationError):
        service.run_image_generation(ImageGenerationInput(prompt=""))
