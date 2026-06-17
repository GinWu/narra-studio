from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import MockAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import CapabilityRequest
from backend.app.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import Asset, CostRecord, Experiment, VoiceProfile
from backend.app.services.credential_resolver import ResolvedCredential
from backend.app.services.asset_service import AssetService, FileService
from backend.app.services.audio_input_validator import AudioInputValidationError, AudioInputValidator
from backend.app.services.audio_lab_service import AudioLabService, SttRunInput, VoiceCloneRunInput
from backend.app.services.model_registry_service import ModelRegistryService
from backend.app.services.project_service import ProjectService
from backend.app.services.provider_service import ProviderService
from backend.app.services.voice_lab_service import TtsRunInput, VoiceLabService
from backend.app.services.voice_profile_service import VoiceProfileError, VoiceProfileService


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
        yield session, tmp_path
    Base.metadata.drop_all(engine)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        service_name="api",
        api_host="0.0.0.0",
        api_port=8000,
        database_url="sqlite://",
        sqlite_dev_url="sqlite://",
        redis_url="redis://redis:6379/0",
        workspace_root=tmp_path,
        log_level="INFO",
        enable_auto_migrations=False,
    )


def _registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(MockAdapter())
    return registry


def _seed_audio_stack(session):
    provider = ProviderService(session).create_provider(
        {
            "name": "mock",
            "provider_type": "mock",
            "credential_source": "none",
            "enabled": True,
            "status": "active",
            "adapter_name": "mock",
        }
    )
    ModelRegistryService(session).seed_mock_models(provider.id)
    return provider


def _audio_asset(session, tmp_path: Path) -> Asset:
    return FileService(AssetService(session, settings=_settings(tmp_path))).save_upload_bytes(
        asset_type="audio",
        filename="sample.wav",
        content=b"mock wav bytes",
        mime_type="audio/wav",
    )


def test_b13_model_seed_registers_stt_and_voice_clone(db_session):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    service = ModelRegistryService(session)

    assert service.get_default_model("stt").adapter_key == "mock"
    assert service.get_default_model("voice_clone").adapter_key == "mock"
    tts = service.get_default_model("tts")
    assert tts.metadata_json["supports_voice_profile"] is True
    assert {model.capability_type for model in service.list_models(provider_id=provider.id)} >= {"tts", "stt", "voice_clone"}


def test_b13_audio_input_validator_rejects_non_audio_and_missing_file(db_session, tmp_path):
    session, _ = db_session
    image = FileService(AssetService(session, settings=_settings(tmp_path))).save_upload_bytes(
        asset_type="image",
        filename="image.png",
        content=b"png",
        mime_type="image/png",
    )
    validator = AudioInputValidator(session)

    with pytest.raises(AudioInputValidationError) as non_audio:
        validator.validate_audio_asset(image.id)
    assert non_audio.value.code == "AUDIO_INPUT_INVALID"

    audio = _audio_asset(session, tmp_path)
    (tmp_path / audio.relative_path).unlink()
    with pytest.raises(AudioInputValidationError) as missing:
        validator.validate_audio_asset(audio.id)
    assert missing.value.code == "AUDIO_INPUT_NOT_FOUND"


def test_b13_mock_stt_creates_transcript_asset_cost_and_output_text(db_session, tmp_path):
    session, _ = db_session
    _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)

    outcome = AudioLabService(session, _registry()).run_stt(SttRunInput(audio_asset_id=audio.id))
    experiment = outcome.capability_outcome.experiment

    assert experiment.status == "success"
    assert experiment.capability_type == "stt"
    assert experiment.output_text == "Mock transcript generated from audio."
    assert experiment.output_asset_refs_json
    transcript = session.get(Asset, experiment.output_asset_refs_json[0]["asset_id"])
    assert transcript.asset_type == "text"
    assert transcript.metadata_json["file_role"] == "transcript"
    assert (tmp_path / transcript.relative_path).read_text() == experiment.output_text
    assert session.scalars(select(CostRecord).where(CostRecord.experiment_id == experiment.id)).first() is not None


def test_b13_mock_voice_clone_creates_voice_profile_and_cost(db_session, tmp_path):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)

    outcome = AudioLabService(session, _registry()).run_voice_clone(
        VoiceCloneRunInput(reference_audio_asset_ids=[audio.id], voice_name="Narrator")
    )
    experiment = outcome.capability_outcome.experiment

    assert experiment.status == "success"
    assert outcome.voice_profile is not None
    assert outcome.voice_profile.provider_id == provider.id
    assert outcome.voice_profile.voice_id
    assert experiment.metadata_json["voice_profile_id"] == outcome.voice_profile.id
    assert session.scalars(select(CostRecord).where(CostRecord.experiment_id == experiment.id)).first() is not None


def test_b13_runtime_audio_file_path_is_not_persisted(db_session, tmp_path):
    session, _ = db_session
    _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)

    outcome = AudioLabService(session, _registry()).run_stt(SttRunInput(audio_asset_id=audio.id))
    experiment = outcome.capability_outcome.experiment
    serialized = str(
        {
            "input_json": experiment.input_json,
            "normalized_params_json": experiment.normalized_params_json,
            "raw_response_json": experiment.raw_response_json,
            "metadata_json": experiment.metadata_json,
        }
    )

    assert audio.id in serialized
    assert str(tmp_path) not in serialized
    assert audio.relative_path not in serialized


def test_b13_mock_adapter_generic_run_supports_voice_clone(db_session):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    model = ModelRegistryService(session).get_default_model("voice_clone")

    result = MockAdapter().run(
        CapabilityRequest(
            request_id="req_test",
            experiment_id="exp_test",
            capability_type="voice_clone",
            provider=provider,
            model=model,
            credential=ResolvedCredential(source="none", value=None, reference=None),
            input_json={"voice_name": "Narrator"},
            params_json={},
        )
    )

    assert result.status == "success"
    assert result.output_files == []
    assert result.metadata["provider_voice_id"].startswith("mock_voice_")


def test_b13_voice_clone_profile_save_failure_marks_experiment_failed(db_session, tmp_path, monkeypatch):
    session, _ = db_session
    _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)

    def fail_create_from_clone_result(self, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(VoiceProfileService, "create_from_clone_result", fail_create_from_clone_result)

    with pytest.raises(VoiceProfileError) as exc:
        AudioLabService(session, _registry()).run_voice_clone(
            VoiceCloneRunInput(reference_audio_asset_ids=[audio.id], voice_name="Narrator")
        )

    assert exc.value.code == "VOICE_PROFILE_SAVE_FAILED"
    experiment = session.scalars(select(Experiment).where(Experiment.capability_type == "voice_clone")).one()
    assert experiment.status == "failed"
    assert experiment.error_json["error_type"] == "voice_profile_save_failed"
    assert session.scalars(select(VoiceProfile)).first() is None


def test_b13_voice_profile_tts_validates_provider_status_and_metadata(db_session, tmp_path):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)
    profile = VoiceProfileService(session).create_from_clone_result(
        provider=provider,
        provider_voice_id="mock-voice-id",
        voice_name="Narrator",
        source_audio_asset_ids=[audio.id],
        sample_asset_id=audio.id,
        consent_status="granted",
        status="active",
    )

    outcome = VoiceLabService(session, _registry()).run_tts(
        TtsRunInput(text="Hello", voice_config={"voice_profile_id": profile.id})
    )
    experiment = outcome.experiment
    asset = session.get(Asset, experiment.output_asset_refs_json[0]["asset_id"])

    assert experiment.status == "success"
    assert experiment.normalized_params_json["voice_profile_id"] == profile.id
    assert experiment.normalized_params_json["voice_id"] == "mock-voice-id"
    assert experiment.metadata_json["voice_profile_id"] == profile.id
    assert asset.metadata_json["voice_profile_id"] == profile.id

    VoiceProfileService(session).mark_revoked(profile.id)
    with pytest.raises(VoiceProfileError) as revoked:
        VoiceLabService(session, _registry()).run_tts(
            TtsRunInput(text="Hello", voice_config={"voice_profile_id": profile.id})
        )
    assert revoked.value.code == "VOICE_PROFILE_REVOKED"


def test_b13_voice_profile_tts_rejects_expired_high_risk_and_commercial_use(db_session):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    service = VoiceProfileService(session)

    expired = service.create_from_clone_result(
        provider=provider,
        provider_voice_id="expired-voice-id",
        voice_name="Expired",
        consent_status="granted",
        status="active",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    with pytest.raises(VoiceProfileError) as expired_error:
        VoiceLabService(session, _registry()).run_tts(
            TtsRunInput(text="Hello", voice_config={"voice_profile_id": expired.id})
        )
    assert expired_error.value.code == "VOICE_PROFILE_EXPIRED"

    high_risk = service.create_from_clone_result(
        provider=provider,
        provider_voice_id="high-risk-voice-id",
        voice_name="High Risk",
        consent_status="granted",
        status="active",
        risk_level="high",
    )
    with pytest.raises(VoiceProfileError) as high_risk_error:
        VoiceLabService(session, _registry()).run_tts(
            TtsRunInput(text="Hello", voice_config={"voice_profile_id": high_risk.id})
        )
    assert high_risk_error.value.code == "VOICE_PROFILE_EXPLICIT_CONFIRM_REQUIRED"

    personal_only = service.create_from_clone_result(
        provider=provider,
        provider_voice_id="personal-voice-id",
        voice_name="Personal",
        consent_status="granted",
        status="active",
        commercial_allowed=False,
    )
    with pytest.raises(VoiceProfileError) as commercial_error:
        VoiceLabService(session, _registry()).run_tts(
            TtsRunInput(text="Hello", voice_config={"voice_profile_id": personal_only.id}, commercial_use=True)
        )
    assert commercial_error.value.code == "VOICE_PROFILE_COMMERCIAL_NOT_ALLOWED"


def test_b13_voice_profile_provider_mismatch_is_rejected(db_session, tmp_path):
    session, _ = db_session
    first = _seed_audio_stack(session)
    second = ProviderService(session).create_provider(
        {
            "name": "mock_other",
            "provider_type": "mock",
            "credential_source": "none",
            "enabled": True,
            "status": "active",
            "adapter_name": "mock",
        }
    )
    other_tts = ModelRegistryService(session).create_model(
        {
            "provider_id": second.id,
            "name": "other-tts",
            "capability_type": "tts",
            "adapter_key": "mock",
            "is_default": False,
        }
    )
    profile = VoiceProfileService(session).create_from_clone_result(
        provider=first,
        provider_voice_id="mock-voice-id",
        voice_name="Narrator",
        consent_status="granted",
        status="active",
    )

    with pytest.raises(VoiceProfileError) as mismatch:
        VoiceLabService(session, _registry()).run_tts(
            TtsRunInput(text="Hello", model_id=other_tts.id, voice_config={"voice_profile_id": profile.id})
        )
    assert mismatch.value.code == "VOICE_PROFILE_PROVIDER_MISMATCH"


def test_b13_voice_profile_update_and_project_default_reject_invalid_state(db_session):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    project = ProjectService(session).create_project({"name": "Audio Project"})
    service = VoiceProfileService(session)
    profile = service.create_from_clone_result(
        provider=provider,
        provider_voice_id="mock-voice-id",
        voice_name="Narrator",
        consent_status="granted",
        status="active",
    )

    with pytest.raises(VoiceProfileError) as invalid:
        service.update_voice_profile(profile.id, {"status": "not-a-state"})
    assert invalid.value.code == "VOICE_PROFILE_STATUS_INVALID"

    service.mark_revoked(profile.id)
    with pytest.raises(VoiceProfileError) as revoked_default:
        service.set_project_default_voice_profile(project.id, profile.id)
    assert revoked_default.value.code == "VOICE_PROFILE_STATUS_INVALID"


def test_b13_transcript_to_script_and_shot_voiceover(db_session, tmp_path):
    session, _ = db_session
    provider = _seed_audio_stack(session)
    audio = _audio_asset(session, tmp_path)
    stt = AudioLabService(session, _registry()).run_stt(SttRunInput(audio_asset_id=audio.id))
    transcript_id = stt.capability_outcome.experiment.output_asset_refs_json[0]["asset_id"]
    project = ProjectService(session).create_project({"name": "Audio Project"})

    script = ProjectService(session).create_script_from_transcript(
        project_id=project.id,
        transcript_asset_id=transcript_id,
        title="Transcript Draft",
    )
    assert script.content == "Mock transcript generated from audio."

    profile = VoiceProfileService(session).create_from_clone_result(
        provider=provider,
        provider_voice_id="mock-voice-id",
        voice_name="Narrator",
        consent_status="granted",
        status="active",
    )
    VoiceProfileService(session).set_project_default_voice_profile(project.id, profile.id)
    shot = ProjectService(session).create_shot(
        project_id=project.id,
        name="Shot 1",
        voiceover_text="A short narration.",
    )
    outcome = VoiceLabService(session, _registry()).run_tts(
        TtsRunInput(
            text=shot.voiceover_text,
            voice_config={"voice_profile_id": profile.id},
            project_id=project.id,
            shot_id=shot.id,
        )
    )
    audio_asset_id = outcome.experiment.output_asset_refs_json[0]["asset_id"]
    updated = ProjectService(session).select_shot_asset(shot.id, asset_type="audio", asset_id=audio_asset_id)

    assert updated.selected_audio_asset_id == audio_asset_id
