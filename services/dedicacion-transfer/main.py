# main.py
"""Arranque del microservicio porcentajes-transfer."""
from __future__ import annotations

import uvicorn

from pathlib import Path

from config.logging_config import configure_logging
from config.settings import get_settings
from interface_adapters.api.app import build_app


def main() -> None:
    settings = get_settings()
    configure_logging(Path(settings.log_dir), settings.log_level)
    app = build_app(settings)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port,
                log_level="info")


if __name__ == "__main__":
    main()
