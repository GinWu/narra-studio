"""HTTP-backed provider adapters.

These adapters intentionally return temporary files or source URLs only. Final
Asset creation remains the responsibility of AssetService.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

import httpx

from backend.app.capabilities.types import (
    AdapterHealthResult,
    CapabilityError,
    CapabilityRequest,
    CapabilityResult,
    OutputFile,
)
from backend.app.db.models import Provider
from backend.app.services.credential_resolver import ResolvedCredential


class HttpProviderAdapter:
    name = "http"
    version = "0.1.0"
    supported_capabilities: list[str] = []

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=60.0, follow_redirects=True)

    def supports(self, capability_type: str) -> bool:
        return capability_type in self.supported_capabilities

    def health_check(self, provider: Provider, credential: ResolvedCredential) -> AdapterHealthResult:
        if provider.credential_source != "none" and credential.is_empty:
            return AdapterHealthResult(ok=False, status="error", message="Provider credential is empty.")
        return AdapterHealthResult(ok=True, status="active", message=f"{self.name} adapter is configured.")

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        raise CapabilityError("adapter_not_implemented", "Adapter run is not implemented.")

    def map_error(self, exc: Exception) -> CapabilityError:
        if isinstance(exc, CapabilityError):
            return exc
        if isinstance(exc, httpx.TimeoutException):
            return CapabilityError("provider_timeout", "Provider request timed out.", status="timeout", retryable=True)
        if isinstance(exc, httpx.HTTPStatusError):
            return CapabilityError(
                "provider_http_error",
                f"Provider returned HTTP {exc.response.status_code}.",
                retryable=exc.response.status_code >= 500,
            )
        if isinstance(exc, httpx.HTTPError):
            return CapabilityError("provider_http_error", "Provider request failed.", retryable=True)
        return CapabilityError("provider_error", "Provider adapter failed.")

    def _api_base(self, request: CapabilityRequest, default: str) -> str:
        return (request.model.api_base_override or request.provider.api_base or default).rstrip("/")

    def _require_credential(self, request: CapabilityRequest) -> str:
        if request.credential.is_empty:
            raise CapabilityError("credential_not_found", "Provider credential not found or unreadable.")
        return request.credential.value or ""

    def _temp_file(self, request: CapabilityRequest, extension: str, content: bytes) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"aiwm_{request.request_id}_"))
        path = temp_dir / f"output.{extension}"
        path.write_bytes(content)
        return path


class OpenAIAdapter(HttpProviderAdapter):
    name = "openai"
    version = "0.1.0"
    supported_capabilities = ["tts", "image_generation"]

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        try:
            if request.capability_type == "tts":
                return self._run_tts(request)
            if request.capability_type == "image_generation":
                return self._run_image_generation(request)
            raise CapabilityError("adapter_unsupported_capability", "OpenAI adapter does not support this capability.")
        except Exception as exc:
            raise self.map_error(exc) from exc

    def _run_tts(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        api_base = self._api_base(request, "https://api.openai.com")
        response = self.client.post(
            f"{api_base}/v1/audio/speech",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": request.model.external_model_id or request.model.name,
                "input": request.input_json.get("text") or request.input_json.get("prompt"),
                "voice": request.params_json.get("voice", "alloy"),
                "response_format": request.params_json.get("response_format", "mp3"),
            },
        )
        response.raise_for_status()
        extension = request.params_json.get("response_format", "mp3")
        path = self._temp_file(request, extension, response.content)
        return CapabilityResult(
            status="success",
            result_mode="sync",
            output_files=[
                OutputFile(
                    file_role="audio_output",
                    file_type="audio",
                    mime_type=response.headers.get("content-type") or "audio/mpeg",
                    extension=extension,
                    temp_path=str(path),
                    size_bytes=path.stat().st_size,
                )
            ],
            usage={"characters": len(str(request.input_json.get("text") or ""))},
            raw_response={"status_code": response.status_code},
        )

    def _run_image_generation(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        api_base = self._api_base(request, "https://api.openai.com")
        response = self.client.post(
            f"{api_base}/v1/images/generations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": request.model.external_model_id or request.model.name,
                "prompt": request.input_json.get("prompt"),
                "size": request.params_json.get("size", "1024x1024"),
                "n": request.params_json.get("n", 1),
                "response_format": request.params_json.get("response_format", "b64_json"),
            },
        )
        response.raise_for_status()
        body = response.json()
        outputs: list[OutputFile] = []
        for index, item in enumerate(body.get("data", [])):
            if item.get("b64_json"):
                content = base64.b64decode(item["b64_json"])
                path = self._temp_file(request, f"{index}.png", content)
                outputs.append(
                    OutputFile(
                        file_role="image_output",
                        file_type="image",
                        mime_type="image/png",
                        extension="png",
                        temp_path=str(path),
                        size_bytes=path.stat().st_size,
                    )
                )
            elif item.get("url"):
                outputs.append(
                    OutputFile(
                        file_role="image_output",
                        file_type="image",
                        mime_type="image/png",
                        extension="png",
                        source_url=item["url"],
                    )
                )
        return CapabilityResult(
            status="success" if outputs else "failed",
            result_mode="sync",
            output_files=outputs,
            usage={"images": len(outputs)},
            raw_response={"created": body.get("created"), "output_count": len(outputs)},
        )


class ElevenLabsAdapter(HttpProviderAdapter):
    name = "elevenlabs"
    version = "0.1.0"
    supported_capabilities = ["tts"]

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        try:
            token = self._require_credential(request)
            voice_id = request.params_json.get("voice_id") or request.input_json.get("voice_id")
            if not voice_id:
                raise CapabilityError("missing_voice_id", "ElevenLabs TTS requires voice_id.")
            api_base = self._api_base(request, "https://api.elevenlabs.io")
            response = self.client.post(
                f"{api_base}/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key": token},
                json={
                    "text": request.input_json.get("text") or request.input_json.get("prompt"),
                    "model_id": request.model.external_model_id or request.model.name,
                    "voice_settings": request.params_json.get("voice_settings", {}),
                },
            )
            response.raise_for_status()
            path = self._temp_file(request, "mp3", response.content)
            return CapabilityResult(
                status="success",
                result_mode="sync",
                output_files=[
                    OutputFile(
                        file_role="audio_output",
                        file_type="audio",
                        mime_type=response.headers.get("content-type") or "audio/mpeg",
                        extension="mp3",
                        temp_path=str(path),
                        size_bytes=path.stat().st_size,
                    )
                ],
                usage={"characters": len(str(request.input_json.get("text") or ""))},
                raw_response={"status_code": response.status_code},
            )
        except Exception as exc:
            raise self.map_error(exc) from exc


class BailianAdapter(HttpProviderAdapter):
    name = "bailian"
    version = "0.1.0"
    supported_capabilities = ["tts", "stt", "voice_clone", "image_generation", "video_generation"]

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        try:
            if request.capability_type == "tts":
                return self.run_tts(request)
            if request.capability_type == "stt":
                return self.run_stt(request)
            if request.capability_type == "voice_clone":
                return self.run_voice_clone(request)
            if request.capability_type in {"image_generation", "video_generation"}:
                return self._run_generation(request)
            raise CapabilityError("adapter_unsupported_capability", "Bailian adapter does not support this capability.")
        except Exception as exc:
            raise self.map_error(exc) from exc

    def run_tts(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        response = self.client.post(
            self._endpoint(request, "/compatible-mode/v1/audio/speech"),
            headers=self._headers(token),
            json={
                "model": request.model.external_model_id or request.model.name,
                "input": request.input_json.get("text") or request.input_json.get("prompt"),
                "voice": request.params_json.get("voice_id") or request.params_json.get("voice"),
                "response_format": request.params_json.get("response_format", "mp3"),
                **request.params_json.get("provider_params", {}),
            },
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        extension = request.params_json.get("response_format", "mp3")
        if content_type.startswith("audio/"):
            path = self._temp_file(request, extension, response.content)
            return CapabilityResult(
                status="success",
                result_mode="sync",
                output_files=[
                    OutputFile(
                        file_role="audio_output",
                        file_type="audio",
                        mime_type=content_type,
                        extension=extension,
                        temp_path=str(path),
                        size_bytes=path.stat().st_size,
                    )
                ],
                usage={"characters": len(str(request.input_json.get("text") or ""))},
                raw_response={"status_code": response.status_code, "content_type": content_type},
                metadata={"adapter": self.name},
            )

        body = self._json(response)
        audio_url = self._first_string(body, ("url", "audio_url", "output.audio.url", "output.url", "data.url"))
        audio_b64 = self._first_string(body, ("audio", "b64_json", "output.audio.data", "output.audio.b64_json", "data.audio"))
        if audio_b64:
            path = self._temp_file(request, extension, base64.b64decode(audio_b64))
            output = OutputFile(
                file_role="audio_output",
                file_type="audio",
                mime_type="audio/mpeg" if extension == "mp3" else "audio/wav",
                extension=extension,
                temp_path=str(path),
                size_bytes=path.stat().st_size,
            )
        elif audio_url:
            output = OutputFile(
                file_role="audio_output",
                file_type="audio",
                mime_type="audio/mpeg" if extension == "mp3" else "audio/wav",
                extension=extension,
                source_url=audio_url,
            )
        else:
            raise CapabilityError("provider_empty_output", "Bailian TTS did not return audio.")
        return CapabilityResult(
            status="success",
            result_mode="sync",
            output_files=[output],
            usage=self._usage_from_body(body, default={"characters": len(str(request.input_json.get("text") or ""))}),
            raw_response=self._safe_raw_response(body, request.capability_type),
            metadata={"adapter": self.name},
        )

    def run_stt(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        runtime_file = request.runtime_files.get("audio")
        if runtime_file is None:
            raise CapabilityError("runtime_file_missing", "Bailian STT requires an audio runtime file.")
        with runtime_file.path.open("rb") as audio_handle:
            response = self.client.post(
                self._endpoint(request, "/api/v1/services/audio/asr/transcription"),
                headers=self._headers(token),
                data={
                    "model": request.model.external_model_id or request.model.name,
                    **self._string_params(request),
                },
                files={"file": (runtime_file.filename, audio_handle, runtime_file.mime_type or "application/octet-stream")},
            )
        response.raise_for_status()
        body = self._json(response)
        transcript = self._first_string(
            body,
            (
                "text",
                "transcript",
                "transcription",
                "output.text",
                "output.transcript",
                "output.transcription",
                "data.text",
            ),
        )
        if not transcript:
            raise CapabilityError("provider_empty_output", "Bailian STT did not return transcript text.")
        path = self._temp_file(request, "txt", transcript.encode("utf-8"))
        return CapabilityResult(
            status="success",
            result_mode="sync",
            output_text=transcript,
            output_files=[
                OutputFile(
                    file_role="transcript",
                    file_type="text",
                    mime_type="text/plain",
                    extension="txt",
                    temp_path=str(path),
                    size_bytes=path.stat().st_size,
                    metadata={"source_audio_asset_id": runtime_file.asset_id},
                )
            ],
            usage=self._usage_from_body(body, default={"requests": 1, "unit_type": "request"}),
            cost_usage={"unit_type": "request", "estimated_cost": None, "unknown_cost": True},
            raw_response=self._safe_raw_response(body, request.capability_type),
            metadata={"adapter": self.name, "transcript_format": "plain_text"},
        )

    def run_voice_clone(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        runtime_files = list(request.runtime_files.values())
        if not runtime_files:
            raise CapabilityError("runtime_file_missing", "Bailian voice clone requires audio runtime files.")
        handles = [runtime_file.path.open("rb") for runtime_file in runtime_files]
        try:
            files = [
                ("files", (runtime_file.filename, handle, runtime_file.mime_type or "application/octet-stream"))
                for runtime_file, handle in zip(runtime_files, handles)
            ]
            response = self.client.post(
                self._endpoint(request, "/api/v1/services/audio/voice-clone"),
                headers=self._headers(token),
                data={
                    "model": request.model.external_model_id or request.model.name,
                    "name": request.input_json.get("voice_name") or request.params_json.get("voice_name") or "cloned_voice",
                    **self._string_params(request),
                },
                files=files,
            )
        finally:
            for handle in handles:
                handle.close()
        response.raise_for_status()
        body = self._json(response)
        provider_voice_id = self._first_string(
            body,
            ("voice_id", "provider_voice_id", "output.voice_id", "output.provider_voice_id", "data.voice_id"),
        )
        if not provider_voice_id:
            raise CapabilityError("provider_empty_output", "Bailian voice clone did not return provider voice_id.")
        voice_name = self._first_string(body, ("voice_name", "name", "output.voice_name", "data.name")) or str(
            request.input_json.get("voice_name") or request.params_json.get("voice_name") or provider_voice_id
        )
        return CapabilityResult(
            status="success",
            result_mode="sync",
            usage=self._usage_from_body(body, default={"requests": 1, "unit_type": "request"}),
            cost_usage={"unit_type": "request", "estimated_cost": None, "unknown_cost": True},
            raw_response=self._safe_raw_response(body, request.capability_type),
            metadata={
                "adapter": self.name,
                "provider_voice_id": provider_voice_id,
                "voice_name": voice_name,
                "requires_verification": self._first_value(body, ("requires_verification", "output.requires_verification")),
            },
        )

    def _run_generation(self, request: CapabilityRequest) -> CapabilityResult:
        token = self._require_credential(request)
        response = self.client.post(
            self._endpoint(request, "/api/v1/services/aigc/multimodal-generation/generation"),
            headers=self._headers(token),
            json={
                "model": request.model.external_model_id or request.model.name,
                "input": request.input_json,
                "parameters": {**request.params_json.get("provider_params", {})},
            },
        )
        response.raise_for_status()
        body = response.json()
        outputs = _extract_source_outputs(request.capability_type, body)
        provider_task_id = self._first_string(body, ("task_id", "output.task_id", "data.task_id", "id"))
        return CapabilityResult(
            status="success" if outputs or provider_task_id else "failed",
            result_mode="async_task" if provider_task_id and not outputs else "sync",
            output_files=outputs,
            provider_task_id=provider_task_id,
            usage=self._usage_from_body(body),
            raw_response=self._safe_raw_response(body, request.capability_type),
            metadata={"adapter": self.name},
        )

    def _endpoint(self, request: CapabilityRequest, default_path: str) -> str:
        path = (
            request.params_json.get("endpoint_path")
            or (request.model.metadata_json or {}).get("default_endpoint_path")
            or default_path
        )
        if str(path).startswith("http://") or str(path).startswith("https://"):
            return str(path)
        api_base = self._api_base(request, "https://dashscope.aliyuncs.com")
        return f"{api_base}/{str(path).lstrip('/')}"

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise CapabilityError("provider_invalid_response", "Bailian provider returned invalid JSON.") from exc
        if not isinstance(body, dict):
            raise CapabilityError("provider_invalid_response", "Bailian provider returned unexpected JSON.")
        return body

    def _string_params(self, request: CapabilityRequest) -> dict[str, str]:
        ignored = {"provider_params", "endpoint_path", "mock_provider_voice_id"}
        params = {**request.params_json.get("provider_params", {})}
        params.update({key: value for key, value in request.params_json.items() if key not in ignored})
        return {
            key: str(value)
            for key, value in params.items()
            if value is not None and isinstance(value, (str, int, float, bool))
        }

    def _safe_raw_response(self, body: dict[str, Any], capability_type: str | None = None) -> dict[str, Any]:
        return {
            "request_id": self._first_string(body, ("request_id", "requestId")),
            "task_id": self._first_string(body, ("task_id", "output.task_id", "data.task_id", "id")),
            "status": self._first_string(body, ("status", "output.status", "data.status")),
            "code": self._first_string(body, ("code", "error.code")),
            "output_count": len(_extract_source_outputs(capability_type or "image_generation", body)),
        }

    def _usage_from_body(self, body: dict[str, Any], default: dict[str, Any] | None = None) -> dict[str, Any] | None:
        usage = self._first_value(body, ("usage", "output.usage", "data.usage"))
        if isinstance(usage, dict):
            return usage
        return default

    def _first_string(self, body: dict[str, Any], paths: tuple[str, ...]) -> str | None:
        value = self._first_value(body, paths)
        return value if isinstance(value, str) and value else None

    def _first_value(self, body: dict[str, Any], paths: tuple[str, ...]) -> Any:
        for path in paths:
            value: Any = body
            for part in path.split("."):
                if not isinstance(value, dict) or part not in value:
                    value = None
                    break
                value = value[part]
            if value is not None:
                return value
        return None


class FalAdapter(HttpProviderAdapter):
    name = "fal"
    version = "0.1.0"
    supported_capabilities = ["image_generation", "video_generation"]

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        try:
            endpoint_path = request.params_json.get("endpoint_path")
            if not endpoint_path:
                raise CapabilityError("provider_endpoint_required", "fal adapter requires endpoint_path.")
            token = self._require_credential(request)
            api_base = self._api_base(request, "https://fal.run")
            response = self.client.post(
                f"{api_base}/{endpoint_path.lstrip('/')}",
                headers={"Authorization": f"Key {token}"},
                json={**request.input_json, **request.params_json.get("provider_params", {})},
            )
            response.raise_for_status()
            body = response.json()
            outputs = _extract_source_outputs(request.capability_type, body)
            return CapabilityResult(
                status="success" if outputs else "failed",
                result_mode="sync",
                output_files=outputs,
                raw_response={"output_count": len(outputs)},
            )
        except Exception as exc:
            raise self.map_error(exc) from exc


class ReplicateAdapter(HttpProviderAdapter):
    name = "replicate"
    version = "0.1.0"
    supported_capabilities = ["image_generation", "video_generation"]

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        try:
            version = request.params_json.get("version") or request.model.external_model_id
            if not version:
                raise CapabilityError("provider_model_version_required", "Replicate adapter requires version.")
            token = self._require_credential(request)
            api_base = self._api_base(request, "https://api.replicate.com")
            response = self.client.post(
                f"{api_base}/v1/predictions",
                headers={"Authorization": f"Bearer {token}"},
                json={"version": version, "input": {**request.input_json, **request.params_json.get("provider_params", {})}},
            )
            response.raise_for_status()
            body = response.json()
            outputs = _extract_source_outputs(request.capability_type, body)
            return CapabilityResult(
                status="success" if outputs else "failed",
                result_mode="async_task" if body.get("id") and not outputs else "sync",
                output_files=outputs,
                provider_task_id=body.get("id"),
                raw_response={"id": body.get("id"), "status": body.get("status"), "output_count": len(outputs)},
            )
        except Exception as exc:
            raise self.map_error(exc) from exc


def _extract_source_outputs(capability_type: str, body: dict[str, Any]) -> list[OutputFile]:
    file_type = "video" if capability_type == "video_generation" else "image"
    role = "video_output" if file_type == "video" else "image_output"
    extension = "mp4" if file_type == "video" else "png"
    mime_type = "video/mp4" if file_type == "video" else "image/png"
    urls: list[str] = []
    for key in ("url", "image_url", "video_url"):
        if isinstance(body.get(key), str):
            urls.append(body[key])
    for collection_key in ("images", "videos", "output"):
        value = body.get(collection_key)
        if isinstance(value, str):
            urls.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict) and isinstance(item.get("url"), str):
                    urls.append(item["url"])
    return [
        OutputFile(
            file_role=role,
            file_type=file_type,
            mime_type=mime_type,
            extension=extension,
            source_url=url,
        )
        for url in urls
    ]
