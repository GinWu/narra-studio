"""Credential resolution with a single controlled access point."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from backend.app.db.models import Provider


class CredentialResolutionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ResolvedCredential:
    source: str
    value: str | None
    reference: str | None

    @property
    def is_empty(self) -> bool:
        return self.value is None or self.value == ""


class CredentialResolver:
    def __init__(self, secrets_root: Path | str = "/run/secrets") -> None:
        self.secrets_root = Path(secrets_root)

    def resolve(self, provider: Provider) -> ResolvedCredential:
        source = provider.credential_source
        if source == "none":
            return ResolvedCredential(source=source, value=None, reference=None)
        if source == "env":
            return self._resolve_env(provider)
        if source == "docker_secret":
            return self._resolve_docker_secret(provider)
        if source == "file":
            return self._resolve_file(provider)
        if source == "encrypted_local":
            raise CredentialResolutionError(
                "unsupported_credential_source",
                "encrypted_local credential storage is deferred for this release.",
            )
        raise CredentialResolutionError(
            "unsupported_credential_source",
            "Provider credential_source is not supported.",
        )

    def _resolve_env(self, provider: Provider) -> ResolvedCredential:
        if not provider.credential_ref:
            raise CredentialResolutionError("credential_not_configured", "Provider env credential_ref is required.")
        value = os.getenv(provider.credential_ref)
        if not value:
            raise CredentialResolutionError("credential_not_found", "Provider credential not found or unreadable.")
        return ResolvedCredential(source="env", value=value, reference=provider.credential_ref)

    def _resolve_docker_secret(self, provider: Provider) -> ResolvedCredential:
        path = Path(provider.credential_file) if provider.credential_file else None
        if path is None:
            if not provider.credential_ref:
                raise CredentialResolutionError(
                    "credential_not_configured",
                    "Provider docker_secret credential_ref is required.",
                )
            path = self.secrets_root / provider.credential_ref
        return ResolvedCredential(source="docker_secret", value=self._read_secret_file(path), reference=str(path))

    def _resolve_file(self, provider: Provider) -> ResolvedCredential:
        if not provider.credential_file:
            raise CredentialResolutionError("credential_not_configured", "Provider credential_file is required.")
        path = Path(provider.credential_file)
        return ResolvedCredential(source="file", value=self._read_secret_file(path), reference=str(path))

    def _read_secret_file(self, path: Path) -> str:
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise CredentialResolutionError(
                "credential_not_found",
                "Provider credential not found or unreadable.",
            ) from exc
        if not value:
            raise CredentialResolutionError("credential_not_found", "Provider credential not found or unreadable.")
        return value


def mask_reference(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"
