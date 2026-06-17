from __future__ import annotations

import logging
import subprocess
import sys

from backend.app.config import get_settings
from backend.app.logging_config import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger("aiwm.worker")
    command = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "backend.app.tasks.celery_app:celery_app",
        "worker",
        "--loglevel",
        settings.log_level.upper(),
        "-Q",
        "default,video",
    ]
    logger.info("starting celery worker")
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
