from __future__ import annotations

import base64
import json

import httpx
import pytest

from backend.app.capabilities.adapters import ElevenLabsAdapter, FalAdapter, OpenAIAdapter, ReplicateAdapter
from backend.app.capabilities.types import CapabilityError, CapabilityRequest
from backend.app.db.models import Model, Provider
from backend.app.services.credential_resolver import ResolvedCredential


def _request(capability_type: str, params=None, input_json=None) -> CapabilityRequest:
    provider = Provider(
        id="prv_test",
        name="provider",
        provider_type="cloud_api",
        status="active",
        enabled=True,
        auth_type="bearer_token",
        credential_source="env",
        credential_ref="KEY",
        adapter_name="openai",
    )
    model = Model(
        id="mdl_test",
        provider_id=provider.id,
        name="model",
        capability_type=capability_type,
        adapter_key="openai",
        status="active",
        enabled=True,
    )
    return CapabilityRequest(
        request_id="req_test",
        experiment_id="exp_test",
        capability_type=capability_type,
        provider=provider,
        model=model,
        credential=ResolvedCredential(source="env", value="secret-token", reference="KEY"),
        input_json=input_json or {"text": "hello", "prompt": "a dot"},
        params_json=params or {},
    )


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_openai_tts_returns_temp_audio_and_sends_authorization_header(tmp_path):
    seen_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        assert request.url.path == "/v1/audio/speech"
        return httpx.Response(200, content=b"audio-bytes", headers={"content-type": "audio/mpeg"})

    result = OpenAIAdapter(client=_client(handler)).run(_request("tts", params={"voice": "alloy"}))

    assert seen_headers["authorization"] == "Bearer secret-token"
    assert result.status == "success"
    assert result.output_files[0].temp_path is not None
    assert result.output_files[0].source_url is None


def test_openai_image_generation_decodes_b64_to_temp_image():
    image_bytes = b"png"

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body["response_format"] == "b64_json"
        return httpx.Response(200, json={"created": 1, "data": [{"b64_json": base64.b64encode(image_bytes).decode()}]})

    result = OpenAIAdapter(client=_client(handler)).run(_request("image_generation"))

    assert result.status == "success"
    assert result.output_files[0].file_type == "image"
    assert result.output_files[0].temp_path is not None


def test_elevenlabs_tts_requires_voice_id_and_returns_audio():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["xi-api-key"] == "secret-token"
        assert request.url.path == "/v1/text-to-speech/voice_1"
        return httpx.Response(200, content=b"audio", headers={"content-type": "audio/mpeg"})

    adapter = ElevenLabsAdapter(client=_client(handler))
    result = adapter.run(_request("tts", params={"voice_id": "voice_1"}))

    assert result.status == "success"
    assert result.output_files[0].temp_path is not None

    with pytest.raises(CapabilityError) as exc:
        adapter.run(_request("tts"))
    assert exc.value.code == "missing_voice_id"


def test_fal_and_replicate_skeletons_normalize_source_urls():
    def fal_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Key secret-token"
        return httpx.Response(200, json={"images": [{"url": "https://provider.local/image.png"}]})

    fal_result = FalAdapter(client=_client(fal_handler)).run(
        _request("image_generation", params={"endpoint_path": "model/path"})
    )
    assert fal_result.output_files[0].source_url == "https://provider.local/image.png"

    def replicate_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret-token"
        return httpx.Response(201, json={"id": "pred_1", "status": "starting", "output": []})

    replicate_result = ReplicateAdapter(client=_client(replicate_handler)).run(
        _request("video_generation", params={"version": "abc"})
    )
    assert replicate_result.result_mode == "async_task"
    assert replicate_result.provider_task_id == "pred_1"
