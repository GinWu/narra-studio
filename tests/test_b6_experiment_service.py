from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.models import PromptTemplate
from backend.app.services.experiment_service import ExperimentService


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


def test_experiment_service_creates_sync_and_async_facts(db_session):
    service = ExperimentService(db_session)
    sync_exp = service.create_running(capability_type="tts", input_json={"text": "hello"})
    async_exp = service.create_running(
        capability_type="video_generation",
        input_json={"prompt": "clip"},
        result_mode="async_task",
    )

    assert sync_exp.status == "running"
    assert sync_exp.result_mode == "sync"
    assert async_exp.status == "pending"
    assert async_exp.result_mode == "async_task"


def test_experiment_status_update_filters_and_asset_refs(db_session):
    service = ExperimentService(db_session)
    exp = service.create_running(capability_type="image_generation", input_json={"prompt": "x"})
    updated = service.update_status(
        exp.id,
        status="partial_success",
        output_asset_refs_json=[{"asset_id": "ast_1"}],
        error_json={"error_type": "one_failed"},
    )

    assert updated.status == "partial_success"
    assert updated.output_asset_refs_json == [{"asset_id": "ast_1"}]
    assert updated.finished_at is not None
    assert service.list_experiments(capability_type="image_generation", status="partial_success") == [updated]


def test_experiment_prompt_version_trace_and_rerun_command(db_session):
    prompt = PromptTemplate(
        id="pmt_1",
        name="voice prompt",
        capability_type="tts",
        content="Say {{text}}",
        version=2,
        version_group_id="grp_1",
        content_hash="hash",
        is_latest=True,
    )
    db_session.add(prompt)
    db_session.commit()

    service = ExperimentService(db_session)
    exp = service.create_running(
        capability_type="tts",
        input_json={"text": "hello"},
        normalized_params_json={"voice": "mock"},
        prompt_template_id=prompt.id,
    )
    command = service.build_rerun_command(exp.id)

    assert exp.prompt_template_id == "pmt_1"
    assert command.parent_experiment_id == exp.id
    assert command.prompt_template_id == "pmt_1"
    assert command.params_json == {"voice": "mock"}


def test_experiment_best_and_failed_case_are_independent(db_session):
    service = ExperimentService(db_session)
    exp = service.create_running(capability_type="tts", input_json={"text": "hello"})
    service.mark_best(exp.id)
    updated = service.mark_failed_case(exp.id, failed_reason="bad prosody")

    assert updated.is_best is True
    assert updated.is_failed_case is True
    assert updated.failed_reason == "bad prosody"


def test_experiment_rejects_invalid_status(db_session):
    service = ExperimentService(db_session)
    exp = service.create_running(capability_type="tts", input_json={"text": "hello"})

    with pytest.raises(ValueError):
        service.update_status(exp.id, status="succeeded")
