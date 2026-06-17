"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, MetaData, Numeric, String, Table, Text, UniqueConstraint, func
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


def timestamps() -> list[Column]:
    return [
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    ]


def soft_delete() -> Column:
    return Column("deleted_at", DateTime(timezone=True), nullable=True)


providers = Table(
    "providers",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("name", String(120), nullable=False, unique=True, index=True),
    Column("display_name", String(200), nullable=True),
    Column("provider_type", String(64), nullable=False, default="cloud_api"),
    Column("status", String(32), nullable=False, default="active", index=True),
    Column("enabled", Boolean, nullable=False, default=False, index=True),
    Column("api_base", String(500), nullable=True),
    Column("docker_service_name", String(120), nullable=True),
    Column("auth_type", String(64), nullable=False, default="none"),
    Column("credential_source", String(32), nullable=False, default="none"),
    Column("credential_ref", String(255), nullable=True),
    Column("credential_file", String(500), nullable=True),
    Column("masked_credential", String(120), nullable=True),
    Column("timeout_seconds", Integer, nullable=True),
    Column("retry_policy_json", json_type(), nullable=True),
    Column("rate_limit_note", Text, nullable=True),
    Column("capability_summary_json", json_type(), nullable=True),
    Column("adapter_name", String(120), nullable=True, index=True),
    Column("sdk_package", String(120), nullable=True),
    Column("sdk_version_constraint", String(120), nullable=True),
    Column("config_json", json_type(), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Column("last_health_status", String(32), nullable=True),
    Column("last_health_error", Text, nullable=True),
)

models = Table(
    "models",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=False, index=True),
    Column("name", String(200), nullable=False),
    Column("display_name", String(200), nullable=True),
    Column("external_model_id", String(255), nullable=True),
    Column("capability_type", String(64), nullable=False, index=True),
    Column("adapter_key", String(120), nullable=False, index=True),
    Column("status", String(32), nullable=False, default="active", index=True),
    Column("enabled", Boolean, nullable=False, default=True, index=True),
    Column("is_default", Boolean, nullable=False, default=False),
    Column("api_base_override", String(500), nullable=True),
    Column("input_schema_json", json_type(), nullable=True),
    Column("output_schema_json", json_type(), nullable=True),
    Column("default_params_json", json_type(), nullable=True),
    Column("pricing_json", json_type(), nullable=True),
    Column("limits_json", json_type(), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    UniqueConstraint("provider_id", "name", name="uq_models_provider_id_name"),
    Index("ix_models_provider_capability", "provider_id", "capability_type"),
)

tags = Table(
    "tags",
    metadata,
    *timestamps(),
    Column("id", String(64), primary_key=True),
    Column("name", String(120), nullable=False, unique=True, index=True),
    Column("color", String(32), nullable=True),
)

prompt_templates = Table(
    "prompt_templates",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("name", String(200), nullable=False, index=True),
    Column("capability_type", String(64), nullable=False, index=True),
    Column("content", Text, nullable=False),
    Column("variables_schema_json", json_type(), nullable=True),
    Column("default_values_json", json_type(), nullable=True),
    Column("version", Integer, nullable=False, default=1),
    Column("version_group_id", String(64), nullable=False, index=True),
    Column("parent_template_id", String(64), ForeignKey("prompt_templates.id"), nullable=True),
    Column("content_hash", String(128), nullable=False, index=True),
    Column("is_latest", Boolean, nullable=False, default=True, index=True),
    Column("status", String(32), nullable=False, default="active", index=True),
    Column("rating", Float, nullable=True),
    Column("usage_count", Integer, nullable=False, default=0),
    Column("success_count", Integer, nullable=False, default=0),
    Column("failure_count", Integer, nullable=False, default=0),
    Column("is_favorite", Boolean, nullable=False, default=False),
    Column("notes", Text, nullable=True),
    Column("description", Text, nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_prompt_templates_group_latest", "version_group_id", "is_latest"),
    Index("ix_prompt_templates_capability", "capability_type"),
)

projects = Table(
    "projects",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("name", String(200), nullable=False, index=True),
    Column("description", Text, nullable=True),
    Column("status", String(32), nullable=False, default="active", index=True),
    Column("metadata_json", json_type(), nullable=True),
    Column("cover_asset_id", String(64), nullable=True),
    Column("final_asset_id", String(64), nullable=True),
)

experiments = Table(
    "experiments",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("title", String(200), nullable=True),
    Column("request_id", String(80), nullable=True, index=True),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=True, index=True),
    Column("model_id", String(64), ForeignKey("models.id"), nullable=True, index=True),
    Column("prompt_template_id", String(64), ForeignKey("prompt_templates.id"), nullable=True),
    Column("parent_experiment_id", String(64), ForeignKey("experiments.id"), nullable=True),
    Column("project_id", String(64), ForeignKey("projects.id"), nullable=True, index=True),
    Column("shot_id", String(64), nullable=True, index=True),
    Column("capability_type", String(64), nullable=False, index=True),
    Column("status", String(32), nullable=False, default="running", index=True),
    Column("result_mode", String(32), nullable=False, default="sync", index=True),
    Column("adapter_name", String(120), nullable=True),
    Column("adapter_version", String(80), nullable=True),
    Column("input_json", json_type(), nullable=False, default=dict),
    Column("normalized_params_json", json_type(), nullable=True),
    Column("output_json", json_type(), nullable=True),
    Column("output_asset_refs_json", json_type(), nullable=True),
    Column("provider_task_id", String(255), nullable=True, index=True),
    Column("usage_json", json_type(), nullable=True),
    Column("cost_usage_json", json_type(), nullable=True),
    Column("raw_response_json", json_type(), nullable=True),
    Column("error_json", json_type(), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Column("duration_ms", Integer, nullable=True),
    Column("is_best", Boolean, nullable=False, default=False, index=True),
    Column("is_failed_case", Boolean, nullable=False, default=False, index=True),
    Column("failed_reason", Text, nullable=True),
    Column("notes", Text, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Index("ix_experiments_capability_status", "capability_type", "status"),
    Index("ix_experiments_project_shot", "project_id", "shot_id"),
)

assets = Table(
    "assets",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("asset_type", String(32), nullable=False, index=True),
    Column("status", String(32), nullable=False, default="active", index=True),
    Column("relative_path", String(1000), nullable=False),
    Column("filename", String(255), nullable=True),
    Column("mime_type", String(120), nullable=True),
    Column("size_bytes", Integer, nullable=True),
    Column("sha256", String(64), nullable=True, index=True),
    Column("width", Integer, nullable=True),
    Column("height", Integer, nullable=True),
    Column("duration_ms", Integer, nullable=True),
    Column("source_experiment_id", String(64), ForeignKey("experiments.id"), nullable=True),
    Column("project_id", String(64), ForeignKey("projects.id"), nullable=True, index=True),
    Column("rating", Float, nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_assets_project_type", "project_id", "asset_type"),
    Index("ix_assets_source_experiment", "source_experiment_id"),
)

asset_versions = Table(
    "asset_versions",
    metadata,
    *timestamps(),
    Column("id", String(64), primary_key=True),
    Column("asset_id", String(64), ForeignKey("assets.id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("relative_path", String(1000), nullable=False),
    Column("mime_type", String(120), nullable=True),
    Column("size_bytes", Integer, nullable=True),
    Column("sha256", String(64), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    UniqueConstraint("asset_id", "version", name="uq_asset_versions_asset_id_version"),
    Index("ix_asset_versions_asset", "asset_id"),
)

evaluations = Table(
    "evaluations",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("target_type", String(32), nullable=False, index=True),
    Column("target_id", String(64), nullable=False, index=True),
    Column("experiment_id", String(64), ForeignKey("experiments.id"), nullable=True),
    Column("asset_id", String(64), ForeignKey("assets.id"), nullable=True),
    Column("prompt_template_id", String(64), ForeignKey("prompt_templates.id"), nullable=True),
    Column("dimension", String(120), nullable=False),
    Column("score", Float, nullable=True),
    Column("label", String(120), nullable=True),
    Column("comment", Text, nullable=True),
    Column("evaluator_id", String(120), nullable=False, default="local"),
    Column("is_best", Boolean, nullable=False, default=False),
    Column("is_failed_case", Boolean, nullable=False, default=False),
    Column("is_active", Boolean, nullable=False, default=True, index=True),
    Column("replaced_by_evaluation_id", String(64), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
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

cost_records = Table(
    "cost_records",
    metadata,
    *timestamps(),
    Column("id", String(64), primary_key=True),
    Column("experiment_id", String(64), ForeignKey("experiments.id"), nullable=False),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=True),
    Column("model_id", String(64), ForeignKey("models.id"), nullable=True),
    Column("capability_type", String(64), nullable=False, index=True),
    Column("usage_json", json_type(), nullable=True),
    Column("normalized_usage_json", json_type(), nullable=True),
    Column("pricing_snapshot_json", json_type(), nullable=True),
    Column("estimated_cost", Numeric(18, 8), nullable=True),
    Column("currency", String(16), nullable=True),
    Index("ix_cost_records_experiment", "experiment_id"),
    Index("ix_cost_records_provider_model", "provider_id", "model_id"),
    Index("ix_cost_records_currency", "currency"),
)

invocation_logs = Table(
    "invocation_logs",
    metadata,
    *timestamps(),
    Column("id", String(64), primary_key=True),
    Column("experiment_id", String(64), ForeignKey("experiments.id"), nullable=True),
    Column("task_id", String(64), nullable=True),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=True),
    Column("model_id", String(64), ForeignKey("models.id"), nullable=True),
    Column("capability_type", String(64), nullable=True),
    Column("status", String(32), nullable=False),
    Column("request_summary_json", json_type(), nullable=True),
    Column("response_summary_json", json_type(), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Column("error_json", json_type(), nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("duration_ms", Integer, nullable=True),
    Index("ix_invocation_logs_experiment", "experiment_id"),
    Index("ix_invocation_logs_task", "task_id"),
    Index("ix_invocation_logs_provider_model", "provider_id", "model_id"),
)

tasks = Table(
    "tasks",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("task_type", String(120), nullable=False, index=True),
    Column("status", String(32), nullable=False, default="pending", index=True),
    Column("progress", Float, nullable=True),
    Column("queue_name", String(120), nullable=True),
    Column("priority", Integer, nullable=False, default=0),
    Column("celery_task_id", String(255), nullable=True),
    Column("provider_task_id", String(255), nullable=True, index=True),
    Column("provider_status", String(120), nullable=True),
    Column("run_mode", String(32), nullable=False, default="async_task"),
    Column("experiment_id", String(64), ForeignKey("experiments.id"), nullable=True),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=True),
    Column("model_id", String(64), ForeignKey("models.id"), nullable=True),
    Column("request_json", json_type(), nullable=True),
    Column("result_json", json_type(), nullable=True),
    Column("error_json", json_type(), nullable=True),
    Column("retry_count", Integer, nullable=False, default=0),
    Column("max_retries", Integer, nullable=False, default=0),
    Column("timeout_seconds", Integer, nullable=True),
    Column("cancel_requested", Boolean, nullable=False, default=False),
    Column("cancel_requested_at", DateTime(timezone=True), nullable=True),
    Column("queued_at", DateTime(timezone=True), nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("last_heartbeat_at", DateTime(timezone=True), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_tasks_experiment", "experiment_id"),
)

voice_profiles = Table(
    "voice_profiles",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("name", String(200), nullable=False, index=True),
    Column("provider_id", String(64), ForeignKey("providers.id"), nullable=True),
    Column("external_voice_id", String(255), nullable=True),
    Column("source_asset_id", String(64), ForeignKey("assets.id"), nullable=True),
    Column("authorization_status", String(32), nullable=False, default="draft", index=True),
    Column("consent_reference", String(500), nullable=True),
    Column("consent_expires_at", DateTime(timezone=True), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
)

project_items = Table(
    "project_items",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("project_id", String(64), ForeignKey("projects.id"), nullable=False),
    Column("item_type", String(32), nullable=False),
    Column("target_id", String(64), nullable=False),
    Column("role", String(80), nullable=True),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_project_items_project", "project_id"),
    Index("ix_project_items_target", "item_type", "target_id"),
)

script_versions = Table(
    "script_versions",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("project_id", String(64), ForeignKey("projects.id"), nullable=False),
    Column("version", Integer, nullable=False),
    Column("title", String(200), nullable=True),
    Column("content", Text, nullable=False),
    Column("status", String(32), nullable=False, default="draft", index=True),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_script_versions_project", "project_id"),
)

shots = Table(
    "shots",
    metadata,
    *timestamps(),
    soft_delete(),
    Column("id", String(64), primary_key=True),
    Column("project_id", String(64), ForeignKey("projects.id"), nullable=False),
    Column("script_version_id", String(64), ForeignKey("script_versions.id"), nullable=True),
    Column("name", String(200), nullable=False),
    Column("description", Text, nullable=True),
    Column("status", String(32), nullable=False, default="draft", index=True),
    Column("prompt_json", json_type(), nullable=True),
    Column("selected_image_asset_id", String(64), nullable=True),
    Column("selected_audio_asset_id", String(64), nullable=True),
    Column("selected_video_asset_id", String(64), nullable=True),
    Column("metadata_json", json_type(), nullable=True),
    Index("ix_shots_project", "project_id"),
    Index("ix_shots_script_version", "script_version_id"),
)

experiment_tags = Table(
    "experiment_tags",
    metadata,
    Column("experiment_id", String(64), ForeignKey("experiments.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)

asset_tags = Table(
    "asset_tags",
    metadata,
    Column("asset_id", String(64), ForeignKey("assets.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)

prompt_template_tags = Table(
    "prompt_template_tags",
    metadata,
    Column("prompt_template_id", String(64), ForeignKey("prompt_templates.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tags.id"), primary_key=True),
)


def upgrade() -> None:
    metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind())
