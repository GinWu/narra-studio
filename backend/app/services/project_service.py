"""Content project organization services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Asset, Experiment, Project, ProjectItem, ScriptVersion, Shot
from backend.app.utils.ids import new_id


class ProjectService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_project(self, data: dict[str, Any]) -> Project:
        project = Project(id=data.pop("id", new_id("proj")), status=data.pop("status", "active"), **data)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: str) -> Project:
        project = self.session.get(Project, project_id)
        if project is None or project.deleted_at is not None:
            raise KeyError("project_not_found")
        return project

    def list_projects(self, status: str | None = None) -> list[Project]:
        stmt = select(Project).where(Project.deleted_at.is_(None)).order_by(Project.updated_at.desc())
        if status:
            stmt = stmt.where(Project.status == status)
        return list(self.session.scalars(stmt).all())

    def update_project(self, project_id: str, data: dict[str, Any]) -> Project:
        project = self.get_project(project_id)
        for key in {"name", "description", "status", "metadata_json", "cover_asset_id", "final_asset_id"}:
            if key in data:
                setattr(project, key, data[key])
        self.session.commit()
        self.session.refresh(project)
        return project

    def delete_project(self, project_id: str) -> Project:
        project = self.get_project(project_id)
        project.status = "deleted"
        project.deleted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(project)
        return project

    def add_item(
        self,
        *,
        project_id: str,
        item_type: str,
        target_id: str,
        role: str | None = None,
        sort_order: int = 0,
        metadata_json: dict[str, Any] | None = None,
    ) -> ProjectItem:
        self.get_project(project_id)
        self._validate_target(item_type, target_id)
        item = ProjectItem(
            id=new_id("pitem"),
            project_id=project_id,
            item_type=item_type,
            target_id=target_id,
            role=role,
            sort_order=sort_order,
            metadata_json=metadata_json,
        )
        if item_type == "asset":
            asset = self.session.get(Asset, target_id)
            if asset and asset.project_id is None:
                asset.project_id = project_id
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def list_items(self, project_id: str) -> list[ProjectItem]:
        self.get_project(project_id)
        stmt = (
            select(ProjectItem)
            .where(ProjectItem.deleted_at.is_(None))
            .where(ProjectItem.project_id == project_id)
            .order_by(ProjectItem.sort_order, ProjectItem.created_at)
        )
        return list(self.session.scalars(stmt).all())

    def create_script_version(
        self,
        *,
        project_id: str,
        content: str,
        title: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ScriptVersion:
        self.get_project(project_id)
        version = len(self.list_script_versions(project_id)) + 1
        script = ScriptVersion(
            id=new_id("script"),
            project_id=project_id,
            version=version,
            title=title,
            content=content,
            status="draft",
            metadata_json=metadata_json,
        )
        self.session.add(script)
        self.session.commit()
        self.session.refresh(script)
        self.add_item(project_id=project_id, item_type="script_version", target_id=script.id, role="script")
        return script

    def list_script_versions(self, project_id: str) -> list[ScriptVersion]:
        stmt = select(ScriptVersion).where(ScriptVersion.deleted_at.is_(None)).where(ScriptVersion.project_id == project_id)
        return list(self.session.scalars(stmt.order_by(ScriptVersion.version)).all())

    def create_shot(
        self,
        *,
        project_id: str,
        name: str,
        description: str | None = None,
        script_version_id: str | None = None,
        voiceover_text: str | None = None,
        prompt_json: dict[str, Any] | None = None,
    ) -> Shot:
        self.get_project(project_id)
        shot = Shot(
            id=new_id("shot"),
            project_id=project_id,
            script_version_id=script_version_id,
            name=name,
            description=description,
            voiceover_text=voiceover_text,
            prompt_json=prompt_json,
        )
        self.session.add(shot)
        self.session.commit()
        self.session.refresh(shot)
        self.add_item(project_id=project_id, item_type="shot", target_id=shot.id, role="shot")
        return shot

    def select_shot_asset(self, shot_id: str, *, asset_type: str, asset_id: str) -> Shot:
        shot = self.session.get(Shot, shot_id)
        if shot is None or shot.deleted_at is not None:
            raise KeyError("shot_not_found")
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise KeyError("asset_not_found")
        field_by_type = {
            "image": "selected_image_asset_id",
            "audio": "selected_audio_asset_id",
            "video": "selected_video_asset_id",
        }
        field = field_by_type.get(asset_type)
        if field is None:
            raise ValueError("unsupported_shot_asset_type")
        setattr(shot, field, asset_id)
        if asset.project_id is None:
            asset.project_id = shot.project_id
        self.session.commit()
        self.session.refresh(shot)
        return shot

    def update_shot(self, shot_id: str, data: dict[str, Any]) -> Shot:
        shot = self.session.get(Shot, shot_id)
        if shot is None or shot.deleted_at is not None:
            raise KeyError("shot_not_found")
        allowed = {"name", "description", "status", "prompt_json", "voiceover_text", "metadata_json"}
        for key, value in data.items():
            if key in allowed:
                setattr(shot, key, value)
        self.session.commit()
        self.session.refresh(shot)
        return shot

    def create_script_from_transcript(
        self,
        *,
        project_id: str,
        transcript_asset_id: str,
        title: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ScriptVersion:
        self.get_project(project_id)
        asset = self.session.get(Asset, transcript_asset_id)
        if asset is None or asset.deleted_at is not None:
            raise KeyError("transcript_asset_not_found")
        file_role = (asset.metadata_json or {}).get("file_role")
        if asset.asset_type != "text" and file_role != "transcript":
            raise ValueError("asset_is_not_transcript")
        from backend.app.services.asset_service import AssetService
        path = AssetService(self.session).get_download_path(asset.id)
        content = path.read_text(encoding="utf-8")
        metadata = {
            **(metadata_json or {}),
            "source": "transcript_asset",
            "transcript_asset_id": asset.id,
            "source_experiment_id": asset.source_experiment_id,
        }
        return self.create_script_version(project_id=project_id, title=title or "Transcript script", content=content, metadata_json=metadata)

    def _validate_target(self, item_type: str, target_id: str) -> None:
        model_by_type = {
            "asset": Asset,
            "experiment": Experiment,
            "shot": Shot,
            "script_version": ScriptVersion,
        }
        model = model_by_type.get(item_type)
        if model is None:
            raise ValueError("unsupported_project_item_type")
        target = self.session.get(model, target_id)
        if target is None or getattr(target, "deleted_at", None) is not None:
            raise KeyError(f"{item_type}_not_found")
