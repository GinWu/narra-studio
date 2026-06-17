"""TDS-13 Audio Lab incremental schema.

Revision ID: 002_tds13_audio_lab
Revises: 001_initial_schema
Create Date: 2026-06-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from backend.app.db.types import json_type


revision = "002_tds13_audio_lab"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("experiments", sa.Column("output_text", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("voiceover_text", sa.Text(), nullable=True))

    op.add_column("voice_profiles", sa.Column("provider", sa.String(length=120), nullable=True))
    op.add_column("voice_profiles", sa.Column("voice_id", sa.String(length=255), nullable=True))
    op.add_column("voice_profiles", sa.Column("voice_name", sa.String(length=200), nullable=True))
    op.add_column(
        "voice_profiles",
        sa.Column("display_name", sa.String(length=200), nullable=False, server_default=""),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("source_type", sa.String(length=64), nullable=False, server_default="cloned"),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("consent_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.add_column("voice_profiles", sa.Column("consent_type", sa.String(length=64), nullable=True))
    op.add_column("voice_profiles", sa.Column("consent_file_asset_id", sa.String(length=64), nullable=True))
    op.add_column("voice_profiles", sa.Column("sample_asset_id", sa.String(length=64), nullable=True))
    op.add_column("voice_profiles", sa.Column("source_audio_asset_ids_json", json_type(), nullable=True))
    op.add_column("voice_profiles", sa.Column("source_person_note", sa.Text(), nullable=True))
    op.add_column("voice_profiles", sa.Column("usage_scope", sa.String(length=120), nullable=True))
    op.add_column(
        "voice_profiles",
        sa.Column("commercial_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("voice_profiles", sa.Column("allowed_platforms_json", json_type(), nullable=True))
    op.add_column("voice_profiles", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "voice_profiles",
        sa.Column("ai_disclosure_required", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="medium"),
    )
    op.add_column(
        "voice_profiles",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="testing"),
    )

    op.execute(
        """
        UPDATE voice_profiles
        SET
            display_name = COALESCE(NULLIF(display_name, ''), name, 'Voice profile'),
            voice_name = COALESCE(voice_name, name),
            voice_id = COALESCE(voice_id, external_voice_id),
            consent_status = CASE
                WHEN authorization_status IN ('revoked', 'expired') THEN authorization_status
                WHEN authorization_status IN ('authorized', 'active') THEN 'granted'
                ELSE consent_status
            END,
            expires_at = COALESCE(expires_at, consent_expires_at)
        """
    )

    with op.batch_alter_table("voice_profiles") as batch_op:
        batch_op.create_foreign_key(
            "fk_voice_profiles_consent_file_asset_id_assets",
            "assets",
            ["consent_file_asset_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_voice_profiles_sample_asset_id_assets",
            "assets",
            ["sample_asset_id"],
            ["id"],
        )

    op.create_index("ix_voice_profiles_provider_id", "voice_profiles", ["provider_id"])
    op.create_index("ix_voice_profiles_voice_id", "voice_profiles", ["voice_id"])
    op.create_index("ix_voice_profiles_status", "voice_profiles", ["status"])
    op.create_index("ix_voice_profiles_source_type", "voice_profiles", ["source_type"])
    op.create_index("ix_voice_profiles_consent_status", "voice_profiles", ["consent_status"])
    op.create_index("ix_voice_profiles_deleted_at", "voice_profiles", ["deleted_at"])


def downgrade() -> None:
    with op.batch_alter_table("voice_profiles") as batch_op:
        batch_op.drop_constraint("fk_voice_profiles_sample_asset_id_assets", type_="foreignkey")
        batch_op.drop_constraint("fk_voice_profiles_consent_file_asset_id_assets", type_="foreignkey")

    op.drop_index("ix_voice_profiles_deleted_at", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_consent_status", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_source_type", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_status", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_voice_id", table_name="voice_profiles")
    op.drop_index("ix_voice_profiles_provider_id", table_name="voice_profiles")

    for column in (
        "status",
        "risk_level",
        "ai_disclosure_required",
        "expires_at",
        "allowed_platforms_json",
        "commercial_allowed",
        "usage_scope",
        "source_person_note",
        "source_audio_asset_ids_json",
        "sample_asset_id",
        "consent_file_asset_id",
        "consent_type",
        "consent_status",
        "source_type",
        "display_name",
        "voice_name",
        "voice_id",
        "provider",
    ):
        op.drop_column("voice_profiles", column)

    op.drop_column("shots", "voiceover_text")
    op.drop_column("experiments", "output_text")
