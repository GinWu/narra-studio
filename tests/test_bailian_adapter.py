from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.capabilities.adapters import BailianAdapter
from backend.app.capabilities.registry import AdapterRegistry
from backend.app.capabilities.types import CapabilityError, CapabilityRequest, RuntimeFileRef
from backend.app.db.base import Base
from backend.app.db.models import Model, Provider
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


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _request(capability_type: str, *, params=None, input_json=None, runtime_files=None) -> CapabilityRequest:
    provider = Provider(
        id="prv_bailian",
        name="bailian",
        provider_type="model_gateway",
        status="active",
        enabled=True,
        auth_type="bearer_token",
        credential_source="env",
        credential_ref="DASHSCOPE_API_KEY",
        adapter_name="bailian",
        api_base="https://dashscope.aliyuncs.com",
    )
    model = Model(
        id="mdl_bailian",
        provider_id=provider.id,
        name=f"bailian-{capability_type}",
        external_model_id=f"bailian-{capability_type}-model",
        capability_type=capability_type,
        adapter_key="bailian",
        status="active",
        enabled=True,
    )
    return CapabilityRequest(
        request_id="req_bailian",
        experiment_id="exp_bailian",
        capability_type=capability_type,
        provider=provider,
        model=model,
        credential=ResolvedCredential(source="env", value="dashscope-secret", reference="DASHSCOPE_API_KEY"),
        input_json=input_json or {"text": "hello"},
        params_json=params or {},
        runtime_files=runtime_files or {},
    )


def _runtime_file(tmp_path: Path, *, key: str = "audio") -> RuntimeFileRef:
    path = tmp_path / f"{key}.wav"
    path.write_bytes(b"wav-bytes")
    return RuntimeFileRef(
        key=key,
        asset_id=f"ast_{key}",
        path=path,
        filename=path.name,
        mime_type="audio/wav",
    )


def test_bailian_tts_accepts_audio_binary_response():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        seen["path"] = request.url.path
        body = json.loads(request.content.decode("utf-8"))
        assert body["input"] == "hello"
        return httpx.Response(200, content=b"mp3-bytes", headers={"content-type": "audio/mpeg"})

    result = BailianAdapter(client=_client(handler)).run_tts(_request("tts"))

    assert seen == {"authorization": "Bearer dashscope-secret", "path": "/compatible-mode/v1/audio/speech"}
    assert result.status == "success"
    assert result.output_files[0].temp_path is not None
    assert result.output_files[0].source_url is None
    assert result.raw_response["content_type"] == "audio/mpeg"


def test_bailian_tts_accepts_json_base64_audio():
    encoded = base64.b64encode(b"mp3-bytes").decode("ascii")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"request_id": "req_1", "output": {"audio": {"b64_json": encoded}}})

    result = BailianAdapter(client=_client(handler)).run_tts(_request("tts", params={"response_format": "mp3"}))

    assert result.status == "success"
    assert result.output_files[0].temp_path is not None
    assert result.raw_response["request_id"] == "req_1"


def test_bailian_stt_uploads_runtime_file_and_returns_transcript(tmp_path):
    runtime_file = _runtime_file(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        seen["path"] = request.url.path
        content = request.content
        assert b'filename="audio.wav"' in content
        assert b"wav-bytes" in content
        return httpx.Response(200, json={"request_id": "req_2", "output": {"text": "transcribed text"}})

    result = BailianAdapter(client=_client(handler)).run_stt(
        _request("stt", runtime_files={"audio": runtime_file})
    )

    assert seen == {"authorization": "Bearer dashscope-secret", "path": "/api/v1/services/audio/asr/transcription"}
    assert result.status == "success"
    assert result.output_text == "transcribed text"
    assert result.output_files[0].file_type == "text"
    assert result.output_files[0].metadata["source_audio_asset_id"] == "ast_audio"


def test_bailian_voice_clone_uploads_runtime_files_and_returns_voice_metadata(tmp_path):
    first = _runtime_file(tmp_path, key="audio_0")
    second = _runtime_file(tmp_path, key="audio_1")

    def handler(request: httpx.Request) -> httpx.Response:
        content = request.content
        assert b'filename="audio_0.wav"' in content
        assert b'filename="audio_1.wav"' in content
        assert b"name=\"name\"" in content
        return httpx.Response(
            200,
            json={
                "request_id": "req_3",
                "output": {
                    "voice_id": "bailian_voice_1",
                    "voice_name": "Narrator",
                    "requires_verification": False,
                },
            },
        )

    result = BailianAdapter(client=_client(handler)).run_voice_clone(
        _request(
            "voice_clone",
            input_json={"voice_name": "Narrator"},
            runtime_files={"audio_0": first, "audio_1": second},
        )
    )

    assert result.status == "success"
    assert result.metadata["provider_voice_id"] == "bailian_voice_1"
    assert result.metadata["voice_name"] == "Narrator"
    assert result.metadata["requires_verification"] is False


def test_bailian_audio_adapters_require_runtime_files():
    adapter = BailianAdapter(client=_client(lambda request: httpx.Response(500)))

    with pytest.raises(CapabilityError) as stt_error:
        adapter.run_stt(_request("stt"))
    assert stt_error.value.code == "runtime_file_missing"

    with pytest.raises(CapabilityError) as clone_error:
        adapter.run_voice_clone(_request("voice_clone"))
    assert clone_error.value.code == "runtime_file_missing"


def test_bailian_seed_provider_and_models(db_session):
    provider_service = ProviderService(db_session)
    created = provider_service.seed_defaults()
    bailian = next(provider for provider in created if provider.name == "bailian")

    models = ModelRegistryService(db_session).seed_bailian_models(bailian.id)

    assert bailian.credential_ref == "dashscope_api_key"
    assert bailian.adapter_name == "bailian"
    assert {model.capability_type for model in models} == {"tts", "stt", "voice_clone"}
    assert all(model.adapter_key == "bailian" for model in models)
    assert all(model.enabled is False for model in models)


def test_bailian_http_errors_are_mapped_through_capability_run_service(db_session, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-secret")
    provider = ProviderService(db_session).create_provider(
        {
            "name": "bailian-test",
            "credential_source": "env",
            "credential_ref": "DASHSCOPE_API_KEY",
            "enabled": True,
            "status": "active",
            "adapter_name": "bailian",
            "api_base": "https://dashscope.aliyuncs.com",
        }
    )
    ModelRegistryService(db_session).create_model(
        {
            "provider_id": provider.id,
            "name": "bailian-tts-test",
            "capability_type": "tts",
            "adapter_key": "bailian",
            "external_model_id": "qwen-tts",
            "is_default": True,
        }
    )
    registry = AdapterRegistry()
    registry.register(BailianAdapter(client=_client(lambda request: httpx.Response(500, json={"code": "bad"}))))

    outcome = CapabilityRunService(db_session, registry).run(
        CapabilityRunCommand(capability_type="tts", input_json={"text": "hello"})
    )

    assert outcome.result is None
    assert outcome.experiment.status == "failed"
    assert outcome.experiment.error_json["error_type"] == "provider_http_error"
    assert outcome.experiment.error_json["retryable"] is True
