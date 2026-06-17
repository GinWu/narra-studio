from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.services.experiment_service import ExperimentService
from backend.app.services.prompt_template_service import PromptTemplateService, prompt_content_hash


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


def test_prompt_template_hash_is_stable_for_canonical_json():
    first = prompt_content_hash("Say {{text}}", {"b": 2, "a": 1}, {"voice": "calm"})
    second = prompt_content_hash("Say {{text}}", {"a": 1, "b": 2}, {"voice": "calm"})
    assert first == second


def test_semantic_update_creates_new_version_and_preserves_old(db_session):
    service = PromptTemplateService(db_session)
    original = service.create_template(
        {
            "name": "voice",
            "capability_type": "tts",
            "content": "Say {{text}}",
            "variables_schema_json": {"text": {"type": "string"}},
            "default_values_json": {"text": "hello"},
        }
    )

    updated = service.update_template(original.id, {"content": "Narrate {{text}}"})
    db_session.refresh(original)

    assert updated.id != original.id
    assert updated.version == 2
    assert updated.version_group_id == original.version_group_id
    assert updated.parent_template_id == original.id
    assert updated.is_latest is True
    assert original.is_latest is False


def test_non_semantic_update_does_not_create_new_version(db_session):
    service = PromptTemplateService(db_session)
    template = service.create_template(
        {"name": "image", "capability_type": "image_generation", "content": "Draw {{subject}}"}
    )

    updated = service.update_template(template.id, {"notes": "favorite"})

    assert updated.id == template.id
    assert updated.version == 1
    assert updated.notes == "favorite"


def test_prompt_assembler_merges_defaults_and_variables(db_session):
    service = PromptTemplateService(db_session)
    template = service.create_template(
        {
            "name": "image",
            "capability_type": "image_generation",
            "content": "Draw {{subject}} in {style}",
            "default_values_json": {"style": "ink"},
        }
    )

    assert service.assemble(template.id, {"subject": "a tree"}) == "Draw a tree in ink"

    with pytest.raises(KeyError):
        service.assemble(template.id, {})


def test_experiment_points_to_specific_prompt_version(db_session):
    prompt_service = PromptTemplateService(db_session)
    original = prompt_service.create_template(
        {"name": "voice", "capability_type": "tts", "content": "Say {{text}}"}
    )
    new_version = prompt_service.update_template(original.id, {"content": "Narrate {{text}}"})

    experiment = ExperimentService(db_session).create_running(
        capability_type="tts",
        input_json={"text": "hello"},
        prompt_template_id=original.id,
    )

    assert experiment.prompt_template_id == original.id
    assert experiment.prompt_template_id != new_version.id
