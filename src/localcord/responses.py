"""JSON responses shaped like Discord's."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import web


def json_response(data: Any, *, status: int = 200) -> web.Response:
    """Like aiohttp's json_response, but with the bare `application/json`
    content type Discord sends. discord.py compares that header exactly and
    treats anything else, including `; charset=utf-8`, as plain text."""
    return web.Response(
        body=json.dumps(data).encode(), status=status, content_type="application/json"
    )
