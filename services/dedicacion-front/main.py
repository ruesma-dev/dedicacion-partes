# main.py
"""Arranque del microservicio dedicacion-front."""
from __future__ import annotations

import uvicorn

from config.settings import get_settings
from interface_adapters.web.app import build_app


def main() -> None:
    settings = get_settings()
    app = build_app(settings)
    uvicorn.run(
        app, host=settings.front_host, port=settings.front_port, log_level="info"
    )


if __name__ == "__main__":
    main()
