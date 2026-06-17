"""PromptTemplate versioning and assembly."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import PromptTemplate
from backend.app.utils.ids import new_id


SEMANTIC_FIELDS = {"content", "variables_schema_json", "default_values_json"}


def prompt_content_hash(
    content: str,
    variables_schema_json: dict[str, Any] | None,
    default_values_json: dict[str, Any] | None,
) -> str:
    payload = {
        "content": content,
        "variables_schema_json": variables_schema_json or {},
        "default_values_json": default_values_json or {},
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PromptAssembler:
    variable_pattern = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}|{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}")

    def assemble(self, template: PromptTemplate, variables: dict[str, Any] | None = None) -> str:
        values = dict(template.default_values_json or {})
        values.update(variables or {})

        def replace(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2)
            if key not in values:
                raise KeyError(f"missing_prompt_variable:{key}")
            return str(values[key])

        return self.variable_pattern.sub(replace, template.content)


class PromptTemplateService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_template(self, data: dict[str, Any]) -> PromptTemplate:
        template_id = data.pop("id", new_id("pmt"))
        content = data["content"]
        variables_schema = data.get("variables_schema_json")
        default_values = data.get("default_values_json")
        template = PromptTemplate(
            id=template_id,
            version_group_id=data.get("version_group_id") or template_id,
            version=data.get("version", 1),
            content_hash=prompt_content_hash(content, variables_schema, default_values),
            is_latest=True,
            **data,
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template

    def get_template(self, template_id: str) -> PromptTemplate:
        template = self.session.get(PromptTemplate, template_id)
        if template is None or template.deleted_at is not None:
            raise KeyError("prompt_template_not_found")
        return template

    def list_templates(
        self,
        *,
        capability_type: str | None = None,
        version_group_id: str | None = None,
        is_latest: bool | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PromptTemplate]:
        stmt = select(PromptTemplate).where(PromptTemplate.deleted_at.is_(None)).order_by(PromptTemplate.updated_at.desc())
        if capability_type:
            stmt = stmt.where(PromptTemplate.capability_type == capability_type)
        if version_group_id:
            stmt = stmt.where(PromptTemplate.version_group_id == version_group_id)
        if is_latest is not None:
            stmt = stmt.where(PromptTemplate.is_latest.is_(is_latest))
        if status:
            stmt = stmt.where(PromptTemplate.status == status)
        return list(self.session.scalars(stmt.limit(limit).offset(offset)).all())

    def get_latest(self, version_group_id: str) -> PromptTemplate:
        stmt = (
            select(PromptTemplate)
            .where(PromptTemplate.deleted_at.is_(None))
            .where(PromptTemplate.version_group_id == version_group_id)
            .where(PromptTemplate.is_latest.is_(True))
        )
        template = self.session.scalars(stmt).first()
        if template is None:
            raise KeyError("prompt_template_not_found")
        return template

    def update_template(self, template_id: str, data: dict[str, Any]) -> PromptTemplate:
        template = self.get_template(template_id)
        if SEMANTIC_FIELDS.intersection(data):
            return self._create_new_version(template, data)

        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        self.session.commit()
        self.session.refresh(template)
        return template

    def assemble(self, template_id: str, variables: dict[str, Any] | None = None) -> str:
        return PromptAssembler().assemble(self.get_template(template_id), variables)

    def record_usage(self, template_id: str, success: bool) -> PromptTemplate:
        template = self.get_template(template_id)
        template.usage_count += 1
        if success:
            template.success_count += 1
        else:
            template.failure_count += 1
        self.session.commit()
        self.session.refresh(template)
        return template

    def delete_template(self, template_id: str) -> PromptTemplate:
        template = self.get_template(template_id)
        template.status = "deleted"
        template.deleted_at = datetime.now(timezone.utc)
        if template.is_latest:
            template.is_latest = False
        self.session.commit()
        self.session.refresh(template)
        return template

    def _create_new_version(self, current: PromptTemplate, data: dict[str, Any]) -> PromptTemplate:
        latest = self.get_latest(current.version_group_id)
        content = data.get("content", latest.content)
        variables_schema = data.get("variables_schema_json", latest.variables_schema_json)
        default_values = data.get("default_values_json", latest.default_values_json)
        content_hash = prompt_content_hash(content, variables_schema, default_values)
        if content_hash == latest.content_hash:
            return self.update_template_metadata(latest, data)

        latest.is_latest = False
        new_template = PromptTemplate(
            id=new_id("pmt"),
            name=data.get("name", latest.name),
            capability_type=data.get("capability_type", latest.capability_type),
            content=content,
            variables_schema_json=variables_schema,
            default_values_json=default_values,
            version=latest.version + 1,
            version_group_id=latest.version_group_id,
            parent_template_id=latest.id,
            content_hash=content_hash,
            is_latest=True,
            status=data.get("status", latest.status),
            rating=latest.rating,
            is_favorite=latest.is_favorite,
            notes=data.get("notes", latest.notes),
            description=data.get("description", latest.description),
            metadata_json=data.get("metadata_json", latest.metadata_json),
        )
        self.session.add(new_template)
        self.session.commit()
        self.session.refresh(new_template)
        return new_template

    def update_template_metadata(self, template: PromptTemplate, data: dict[str, Any]) -> PromptTemplate:
        for key in {"name", "description", "notes", "status", "rating", "is_favorite", "metadata_json"}:
            if key in data:
                setattr(template, key, data[key])
        self.session.commit()
        self.session.refresh(template)
        return template
