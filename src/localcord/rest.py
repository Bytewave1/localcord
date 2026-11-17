"""The REST API a bot calls, served under /api/v10."""

from __future__ import annotations

from aiohttp import web

from .gateway import gateway_url
from .keys import STATE
from .responses import json_response

routes = web.RouteTableDef()


def _error(status: int, message: str) -> web.Response:
    return json_response({"message": message, "code": 0}, status=status)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    # GET /gateway is the one route Discord serves without a token.
    if request.path.endswith("/gateway") and request.method == "GET":
        return await handler(request)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith(("Bot ", "Bearer ")) or not auth.split(" ", 1)[1].strip():
        return _error(401, "401: Unauthorized")
    return await handler(request)


@routes.get("/gateway")
async def get_gateway(request: web.Request) -> web.Response:
    return json_response({"url": gateway_url(request)})


@routes.get("/gateway/bot")
async def get_gateway_bot(request: web.Request) -> web.Response:
    return json_response(
        {
            "url": gateway_url(request),
            "shards": 1,
            "session_start_limit": {
                "total": 1000,
                "remaining": 1000,
                "reset_after": 0,
                "max_concurrency": 1,
            },
        }
    )


@routes.get("/users/@me")
async def get_current_user(request: web.Request) -> web.Response:
    bot = request.config_dict[STATE].bot
    return json_response({**bot, "verified": True, "mfa_enabled": False, "email": None})


@routes.get("/applications/@me")
@routes.get("/oauth2/applications/@me")
async def get_current_application(request: web.Request) -> web.Response:
    return json_response(request.config_dict[STATE].application)


@routes.route("*", "/{tail:.*}")
async def not_implemented(request: web.Request) -> web.Response:
    return _error(501, f"localcord does not implement {request.method} {request.path} yet")


def create_api_app() -> web.Application:
    api = web.Application(middlewares=[auth_middleware])
    api.add_routes(routes)
    return api
