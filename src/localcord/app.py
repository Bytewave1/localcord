"""Builds the aiohttp application that serves the emulated API."""

from aiohttp import web

from . import __version__

API_PREFIX = "/api/v10"
CONTROL_PREFIX = "/_control"


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "version": __version__})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get(f"{CONTROL_PREFIX}/health", health)
    return app
