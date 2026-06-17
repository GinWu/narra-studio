"""Shared status and type constants persisted by the database models."""

PROVIDER_STATUSES = ("active", "disabled", "error")
CREDENTIAL_SOURCES = ("docker_secret", "env", "file", "none", "encrypted_local")

CAPABILITY_TYPES = (
    "tts",
    "stt",
    "voice_clone",
    "speech_to_text",
    "image_generation",
    "image_edit",
    "image_variation",
    "video_generation",
    "video_edit",
    "llm",
)

EXPERIMENT_STATUSES = (
    "pending",
    "running",
    "success",
    "failed",
    "timeout",
    "cancelled",
    "partial_success",
)
RESULT_MODES = ("sync", "async_task")

ASSET_TYPES = ("audio", "image", "video", "text", "metadata", "other")
ASSET_STATUSES = ("active", "discarded", "deleted")

EVALUATION_TARGET_TYPES = ("experiment", "asset")
TASK_STATUSES = ("pending", "queued", "running", "succeeded", "failed", "timeout", "cancelled")

PROJECT_STATUSES = ("active", "archived", "deleted")
PROJECT_ITEM_TYPES = ("asset", "experiment", "shot", "script_version")
SCRIPT_STATUSES = ("draft", "active", "archived")
SHOT_STATUSES = ("draft", "in_progress", "selected", "discarded")
VOICE_PROFILE_STATUSES = ("active", "testing", "disabled", "revoked", "expired", "draft")
VOICE_PROFILE_CONSENT_STATUSES = ("pending", "granted", "revoked", "expired", "unknown")
INVOCATION_STATUSES = ("success", "failed", "timeout", "cancelled", "partial_success")
