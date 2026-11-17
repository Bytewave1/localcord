"""Builds the aiohttp application that serves the emulated API."""

from __future__ import annotations

from aiohttp import web

from .control import create_control_app
from .gateway import GATEWAY_PATH, gateway_handler
from .keys import STATE
from .rest import create_api_app
from .state import State

# Versioned prefixes first, so "/api" only catches unversioned requests.
API_PREFIXES = ("/api/v10", "/api/v9", "/api")
CONTROL_PREFIX = "/_control"


def create_app(state: State | None = None) -> web.Application:
    app = web.Application()
    app[STATE] = state or State.default()
    app.router.add_get(GATEWAY_PATH, gateway_handler)
    app.add_subapp(CONTROL_PREFIX, create_control_app())
    for prefix in API_PREFIXES:
        app.add_subapp(prefix, create_api_app())
    return app
