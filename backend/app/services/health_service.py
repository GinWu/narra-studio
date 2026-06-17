from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.config import Settings


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def check(self) -> dict[str, Any]:
        database_status = self._check_database()
        storage_status = self._check_storage()
        database_ok = database_status in {"ok", "dev_sqlite_configured"}
        overall = "ok" if database_ok and storage_status == "ok" else "degraded"
        return {
            "status": overall,
            "database": database_status,
            "storage": storage_status,
            "service": self.settings.service_name,
            "workspace": "configured",
        }

    def _check_database(self) -> str:
        if self.settings.database_url.startswith("sqlite"):
            return "dev_sqlite_configured"
        try:
            import psycopg

            with psycopg.connect(self.settings.database_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("select 1")
                    cur.fetchone()
            return "ok"
        except Exception:
            return "unavailable"

    def _check_storage(self) -> str:
        required_dirs = [
            self.settings.assets_root,
            self.settings.uploads_root,
            self.settings.thumbnails_root,
            self.settings.exports_root,
        ]
        try:
            for directory in required_dirs:
                directory.mkdir(parents=True, exist_ok=True)
            probe = self.settings.workspace_root / ".healthcheck"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except OSError:
            return "unavailable"

        if not self._all_inside_workspace(required_dirs):
            return "invalid_path"
        return "ok"

    def _all_inside_workspace(self, paths: list[Path]) -> bool:
        root = self.settings.workspace_root.resolve()
        for path in paths:
            resolved = path.resolve()
            if root != resolved and root not in resolved.parents:
                return False
        return True
