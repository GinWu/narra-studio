from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.enums import TASK_STATUSES
from backend.app.db.models import Asset, CostRecord, Experiment, Provider, Shot, VoiceProfile


def test_core_tables_are_declared():
    expected_tables = {
        "providers",
        "models",
        "prompt_templates",
        "experiments",
        "assets",
        "asset_versions",
        "evaluations",
        "cost_records",
        "invocation_logs",
        "tasks",
        "projects",
        "project_items",
        "script_versions",
        "shots",
        "voice_profiles",
        "tags",
    }
    assert expected_tables.issubset(Base.metadata.tables)


def test_models_preserve_architecture_columns():
    assert "relative_path" in Asset.__table__.columns
    assert "file_path" not in Asset.__table__.columns
    assert "source_experiment_id" in Asset.__table__.columns
    assert "raw_response_json" in Experiment.__table__.columns
    assert CostRecord.__table__.columns["estimated_cost"].nullable is True
    assert Provider.__table__.columns["credential_source"].nullable is False
    assert Provider.__table__.columns["credential_ref"].nullable is True
    assert "output_text" in Experiment.__table__.columns
    assert "voiceover_text" in Shot.__table__.columns
    for column_name in {
        "voice_id",
        "voice_name",
        "display_name",
        "source_type",
        "consent_status",
        "commercial_allowed",
        "risk_level",
        "status",
    }:
        assert column_name in VoiceProfile.__table__.columns


def test_async_task_status_values_match_tds09():
    assert TASK_STATUSES == (
        "pending",
        "queued",
        "running",
        "succeeded",
        "failed",
        "timeout",
        "cancelled",
    )


def test_sqlite_schema_can_initialize_and_store_core_records():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    assert "experiments" in inspector.get_table_names()
    assert "assets" in inspector.get_table_names()
    assert "cost_records" in inspector.get_table_names()

    Session = sessionmaker(bind=engine)
    with Session() as session:
        provider = Provider(
            id="provider_mock",
            name="mock",
            status="active",
            credential_source="none",
        )
        experiment = Experiment(
            id="exp_1",
            capability_type="tts",
            status="running",
            result_mode="sync",
            input_json={"prompt": "hello"},
        )
        session.add_all([provider, experiment])
        session.commit()

    Base.metadata.drop_all(engine)
