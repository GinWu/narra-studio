from __future__ import annotations

import sys

from backend.app.config import get_settings
from backend.app.services.health_service import HealthService


def main() -> int:
    result = HealthService(get_settings()).check()
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

