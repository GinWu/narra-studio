"""Local mock adapter for development, CI, and frontend integration."""

from __future__ import annotations

import base64
import tempfile
from dataclasses import replace
from pathlib import Path
from time import sleep
from typing import Any

from backend.app.capabilities.types import (
    AdapterHealthResult,
    CapabilityError,
    CapabilityRequest,
    CapabilityResult,
    OutputFile,
)
from backend.app.db.models import Provider
from backend.app.services.credential_resolver import ResolvedCredential


class MockAdapter:
    name = "mock"
    version = "0.1.0"
    supported_capabilities = ["tts", "stt", "voice_clone", "image_generation", "video_generation"]

    def supports(self, capability_type: str) -> bool:
        return capability_type in self.supported_capabilities

    def health_check(self, provider: Provider, credential: ResolvedCredential) -> AdapterHealthResult:
        return AdapterHealthResult(ok=True, message="Mock provider is available.", metadata={"provider": provider.name})

    def run(self, request: CapabilityRequest) -> CapabilityResult:
        delay = float(request.params_json.get("mock_delay_seconds", 0) or 0)
        if delay > 0:
            sleep(min(delay, 2))

        status = request.params_json.get("mock_status", "success")
        if status == "raise_timeout":
            raise CapabilityError("mock_timeout", "Mock timeout requested.", status="timeout", retryable=True)
        if status == "raise_error":
            raise CapabilityError("mock_error", "Mock error requested.")
        if status == "failed":
            return CapabilityResult(
                status="failed",
                result_mode="sync",
                error={"error_type": "mock_failed", "message": "Mock failure requested."},
                raw_response={"mock": True, "status": "failed"},
            )
        if status == "timeout":
            return CapabilityResult(
                status="timeout",
                result_mode="sync",
                error={"error_type": "mock_timeout", "message": "Mock timeout requested."},
                raw_response={"mock": True, "status": "timeout"},
            )
        if request.capability_type == "voice_clone":
            result = self.run_voice_clone(request)
            if status == "partial_success":
                result = replace(
                    result,
                    status="partial_success",
                    error={"error_type": "mock_partial", "message": "One mock output failed."},
                    raw_response={"mock": True, "status": "partial_success", "capability": "voice_clone"},
                )
            return result

        output_files = [self._make_output_file(request)]
        if status == "partial_success":
            return CapabilityResult(
                status="partial_success",
                result_mode="sync",
                output_files=output_files,
                usage=self._usage(request),
                cost_usage={"estimated_cost": None, "unknown_cost": True},
                raw_response={"mock": True, "status": "partial_success"},
                error={"error_type": "mock_partial", "message": "One mock output failed."},
                metadata={"adapter": self.name},
            )

        return CapabilityResult(
            status="success",
            result_mode="sync",
            output_text="mock output" if request.capability_type == "tts" else None,
            output_files=output_files,
            usage=self._usage(request),
            cost_usage={"estimated_cost": None, "unknown_cost": True},
            raw_response={"mock": True, "status": "success"},
            metadata={"adapter": self.name},
        )

    def run_tts(self, request: CapabilityRequest) -> CapabilityResult:
        return self.run(request)

    def run_stt(self, request: CapabilityRequest) -> CapabilityResult:
        transcript = str(request.params_json.get("mock_transcript") or "Mock transcript generated from audio.")
        output = self._make_output_file(
            CapabilityRequest(
                request_id=request.request_id,
                experiment_id=request.experiment_id,
                capability_type="stt",
                provider=request.provider,
                model=request.model,
                credential=request.credential,
                input_json={**request.input_json, "transcript": transcript},
                params_json=request.params_json,
                timeout_seconds=request.timeout_seconds,
            )
        )
        return CapabilityResult(
            status="success",
            result_mode="sync",
            output_text=transcript,
            output_files=[output],
            usage={"seconds": request.params_json.get("duration_seconds", 1), "requests": 1, "unit_type": "second"},
            cost_usage={"unit_type": "second", "estimated_cost": None, "unknown_cost": True},
            raw_response={"mock": True, "status": "success", "capability": "stt"},
            metadata={"adapter": self.name, "transcript_format": "plain_text"},
        )

    def run_voice_clone(self, request: CapabilityRequest) -> CapabilityResult:
        voice_name = str(request.input_json.get("voice_name") or request.params_json.get("voice_name") or "Mock cloned voice")
        provider_voice_id = str(request.params_json.get("mock_provider_voice_id") or f"mock_voice_{request.request_id}")
        return CapabilityResult(
            status="success",
            result_mode="sync",
            usage={"requests": 1, "unit_type": "request"},
            cost_usage={"unit_type": "request", "estimated_cost": None, "unknown_cost": True},
            raw_response={"mock": True, "status": "success", "capability": "voice_clone"},
            metadata={
                "adapter": self.name,
                "provider_voice_id": provider_voice_id,
                "voice_name": voice_name,
            },
        )

    def map_error(self, exc: Exception) -> CapabilityError:
        if isinstance(exc, CapabilityError):
            return exc
        return CapabilityError("mock_adapter_error", "Mock adapter failed.")

    def _make_output_file(self, request: CapabilityRequest) -> OutputFile:
        if request.params_json.get("mock_source_url"):
            return OutputFile(
                file_role=self._file_role(request.capability_type),
                file_type=self._file_type(request.capability_type),
                mime_type=self._mime_type(request.capability_type),
                extension=self._extension(request.capability_type),
                source_url=f"https://mock.local/{request.request_id}/{self._filename(request.capability_type)}",
            )

        temp_dir = Path(tempfile.mkdtemp(prefix=f"aiwm_{request.request_id}_"))
        file_path = temp_dir / self._filename(request.capability_type)
        file_path.write_bytes(self._content(request))
        return OutputFile(
            file_role=self._file_role(request.capability_type),
            file_type=self._file_type(request.capability_type),
            mime_type=self._mime_type(request.capability_type),
            extension=self._extension(request.capability_type),
            temp_path=str(file_path),
            size_bytes=file_path.stat().st_size,
            width=1 if request.capability_type == "image_generation" else None,
            height=1 if request.capability_type == "image_generation" else None,
            duration_seconds=1.0 if request.capability_type in {"tts", "video_generation"} else None,
        )

    def _content(self, request: CapabilityRequest) -> bytes:
        if request.capability_type == "image_generation":
            return base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
            )
        if request.capability_type == "video_generation":
            return b"mock mp4 placeholder\n"
        if request.capability_type == "stt":
            return str(request.input_json.get("transcript") or "Mock transcript generated from audio.").encode("utf-8")
        text = str(request.input_json.get("text") or request.input_json.get("prompt") or "mock audio")
        return f"mock wav placeholder: {text}\n".encode("utf-8")

    def _usage(self, request: CapabilityRequest) -> dict[str, Any]:
        if request.capability_type == "tts":
            text = str(request.input_json.get("text") or "")
            return {"characters": len(text), "outputs": 1}
        if request.capability_type == "image_generation":
            return {"images": 1}
        if request.capability_type == "stt":
            return {"seconds": request.params_json.get("duration_seconds", 1), "requests": 1}
        if request.capability_type == "voice_clone":
            return {"requests": 1}
        return {"videos": 1}

    def _file_role(self, capability_type: str) -> str:
        return {
            "tts": "audio_output",
            "stt": "transcript",
            "image_generation": "image_output",
            "video_generation": "video_output",
        }[capability_type]

    def _file_type(self, capability_type: str) -> str:
        return {
            "tts": "audio",
            "stt": "text",
            "image_generation": "image",
            "video_generation": "video",
        }[capability_type]

    def _mime_type(self, capability_type: str) -> str:
        return {
            "tts": "audio/wav",
            "stt": "text/plain",
            "image_generation": "image/png",
            "video_generation": "video/mp4",
        }[capability_type]

    def _extension(self, capability_type: str) -> str:
        return {
            "tts": "wav",
            "stt": "txt",
            "image_generation": "png",
            "video_generation": "mp4",
        }[capability_type]

    def _filename(self, capability_type: str) -> str:
        return f"mock_output.{self._extension(capability_type)}"
