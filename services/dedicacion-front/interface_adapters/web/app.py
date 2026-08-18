# interface_adapters/web/app.py
"""Front de dedicación: sirve la interfaz y hace proxy hacia dedicacion-api.

En Azure este servicio va con ingress externo + Easy Auth (Entra ID); el
backend queda con ingress interno. El proxy inyecta la identidad del
usuario (cabecera X-MS-CLIENT-PRINCIPAL-NAME de Easy Auth) como
X-Usuario para la auditoría del backend.
"""
from __future__ import annotations

import logging
import time

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.settings import BASE_DIR, Settings, get_settings

logger = logging.getLogger(__name__)

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
    "content-encoding", "host",
}


def build_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = FastAPI(title=settings.service_name, version=settings.service_version)
    asset_version = str(int(time.time()))  # cache-buster: cambia al reiniciar

    templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
    app.mount(
        "/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static"
    )
    cliente = httpx.AsyncClient(
        base_url=settings.api_base_url, timeout=settings.api_timeout_s
    )

    @app.on_event("shutdown")
    async def cerrar_cliente() -> None:
        await cliente.aclose()

    # ------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        usuario = _usuario(request, settings)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "usuario": usuario,
                "version": settings.service_version,
                "asset_version": asset_version,
            },
        )

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {
            "ok": True,
            "service": settings.service_name,
            "version": settings.service_version,
        }

    # ------------------------------------------------------------------
    @app.api_route(
        "/api/{ruta:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    async def proxy(request: Request, ruta: str) -> Response:
        """Reenvía la petición al backend conservando método, query y cuerpo."""
        url = f"/api/{ruta}"
        cuerpo = await request.body()
        cabeceras = {
            "x-usuario": _usuario(request, settings),
        }
        if "content-type" in request.headers:
            cabeceras["content-type"] = request.headers["content-type"]
        try:
            respuesta = await cliente.request(
                request.method,
                url,
                params=request.query_params,
                content=cuerpo if cuerpo else None,
                headers=cabeceras,
            )
        except httpx.HTTPError as exc:
            logger.error("Proxy: backend inaccesible: %s", exc)
            return Response(
                content=(
                    '{"error": "Backend dedicacion-api inaccesible"}'
                ),
                status_code=502,
                media_type="application/json",
            )
        cabeceras_salida = {
            k: v
            for k, v in respuesta.headers.items()
            if k.lower() not in _HOP_BY_HOP
        }
        return Response(
            content=respuesta.content,
            status_code=respuesta.status_code,
            headers=cabeceras_salida,
        )

    return app


def _usuario(request: Request, settings: Settings) -> str:
    """Identidad de Easy Auth o usuario por defecto en local."""
    principal = request.headers.get("x-ms-client-principal-name", "").strip()
    return principal or settings.default_user
