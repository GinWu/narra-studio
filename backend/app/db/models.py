"""ORM model definitions for Narra Studio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, SoftDeleteMixin, TimestampMixin
from backend.app.db.types import json_type


experiment_tags = Table(
    "experiment_tags",
    Base.metadata,
    Column("experiment_id", String(64), ForeignKey("experiments.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)

asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", String(64), ForeignKey("assets.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)

prompt_template_tags = Table(
    "prompt_template_tags",
    Base.metadata,
    Column("prompt_template_id", String(64), ForeignKey("prompt_templates.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)


class Provider(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    provider_type: Mapped[str] = mapped_column(String(64), nullable=False, default="cloud_api")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    api_base: Mapped[str | None] = mapped_column(String(500), nullable=True)
    docker_service_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    auth_type: Mapped[str] = mapped_column(String(64), nullable=False, default="none")
    credential_source: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credential_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    masked_credential: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retry_policy_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    rate_limit_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    capability_summary_json: Mapped[list | None] = mapped_column(json_type(), nullable=True)
    adapter_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    sdk_package: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sdk_version_constraint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    last_health_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_health_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Model(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("provider_id", "name", name="uq_models_provider_id_name"),
        Index("ix_models_provider_capability", "provider_id", "capability_type"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(64), ForeignKey("providers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capability_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    adapter_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_base_override: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_schema_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    output_schema_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    default_params_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    pricing_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    limits_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class Tag(TimestampMixin, Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)


class PromptTemplate(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        Index("ix_prompt_templates_group_latest", "version_group_id", "is_latest"),
        Index("ix_prompt_templates_capability", "capability_type"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    capability_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    default_values_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_group_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("prompt_templates.id"), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class Project(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    cover_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    final_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Experiment(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "experiments"
    __table_args__ = (
        Index("ix_experiments_capability_status", "capability_type", "status"),
        Index("ix_experiments_project_shot", "project_id", "shot_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("providers.id"), nullable=True, index=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("models.id"), nullable=True, index=True)
    prompt_template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("prompt_templates.id"), nullable=True)
    parent_experiment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"), nullable=True, index=True)
    shot_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    capability_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", index=True)
    result_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sync", index=True)
    adapter_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    adapter_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_json: Mapped[dict] = mapped_column(json_type(), nullable=False, default=dict)
    normalized_params_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    output_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_asset_refs_json: Mapped[list | None] = mapped_column(json_type(), nullable=True)
    provider_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    usage_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    cost_usage_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    raw_response_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    error_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_best: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_failed_case: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Asset(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_project_type", "project_id", "asset_type"),
        Index("ix_assets_source_experiment", "source_experiment_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    relative_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_experiment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("projects.id"), nullable=True, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class AssetVersion(TimestampMixin, Base):
    __tablename__ = "asset_versions"
    __table_args__ = (
        UniqueConstraint("asset_id", "version", name="uq_asset_versions_asset_id_version"),
        Index("ix_asset_versions_asset", "asset_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class Evaluation(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint(
            "target_type",
            "target_id",
            "dimension",
            "evaluator_id",
            "is_active",
            name="uq_evaluations_active_identity",
        ),
        Index("ix_evaluations_target", "target_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    experiment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=True)
    asset_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("assets.id"), nullable=True)
    prompt_template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("prompt_templates.id"), nullable=True)
    dimension: Mapped[str] = mapped_column(String(120), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluator_id: Mapped[str] = mapped_column(String(120), nullable=False, default="local")
    is_best: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_failed_case: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    replaced_by_evaluation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class CostRecord(TimestampMixin, Base):
    __tablename__ = "cost_records"
    __table_args__ = (
        Index("ix_cost_records_experiment", "experiment_id"),
        Index("ix_cost_records_provider_model", "provider_id", "model_id"),
        Index("ix_cost_records_currency", "currency"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=False)
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("providers.id"), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("models.id"), nullable=True)
    capability_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    usage_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    normalized_usage_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    pricing_snapshot_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)


class InvocationLog(TimestampMixin, Base):
    __tablename__ = "invocation_logs"
    __table_args__ = (
        Index("ix_invocation_logs_experiment", "experiment_id"),
        Index("ix_invocation_logs_task", "task_id"),
        Index("ix_invocation_logs_provider_model", "provider_id", "model_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("providers.id"), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("models.id"), nullable=True)
    capability_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    request_summary_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    response_summary_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    error_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Task(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_experiment", "experiment_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    progress: Mapped[float | None] = mapped_column(Float, nullable=True)
    queue_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    run_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="async_task")
    experiment_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("experiments.id"), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("providers.id"), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("models.id"), nullable=True)
    request_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    result_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    error_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class VoiceProfile(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "voice_profiles"
    __table_args__ = (
        Index("ix_voice_profiles_provider_id", "provider_id"),
        Index("ix_voice_profiles_voice_id", "voice_id"),
        Index("ix_voice_profiles_status", "status"),
        Index("ix_voice_profiles_source_type", "source_type"),
        Index("ix_voice_profiles_consent_status", "consent_status"),
        Index("ix_voice_profiles_deleted_at", "deleted_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("providers.id"), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voice_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="cloned")
    consent_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    consent_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_file_asset_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("assets.id"), nullable=True)
    sample_asset_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("assets.id"), nullable=True)
    source_audio_asset_ids_json: Mapped[list | None] = mapped_column(json_type(), nullable=True)
    source_person_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_scope: Mapped[str | None] = mapped_column(String(120), nullable=True)
    commercial_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_platforms_json: Mapped[list | None] = mapped_column(json_type(), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_disclosure_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="testing")
    # Legacy v0.2 preview columns retained for existing deployments.
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    external_voice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_asset_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("assets.id"), nullable=True)
    authorization_status: Mapped[str | None] = mapped_column(String(32), nullable=True, default="draft", index=True)
    consent_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consent_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class ProjectItem(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "project_items"
    __table_args__ = (
        Index("ix_project_items_project", "project_id"),
        Index("ix_project_items_target", "item_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class ScriptVersion(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "script_versions"
    __table_args__ = (Index("ix_script_versions_project", "project_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)


class Shot(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "shots"
    __table_args__ = (
        Index("ix_shots_project", "project_id"),
        Index("ix_shots_script_version", "script_version_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False)
    script_version_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("script_versions.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    prompt_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
    selected_image_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_audio_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_video_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    voiceover_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(json_type(), nullable=True)
