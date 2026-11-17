"""The control API under /_control: how tests inspect and drive the emulator.

These routes do not exist on Discord.
"""

from __future__ import annotations

from aiohttp import web

from . import __version__
from .keys import STATE
from .responses import json_response

routes = web.RouteTableDef()


@routes.get("/health")
async def health(request: web.Request) -> web.Response:
    return json_response({"status": "ok", "version": __version__})


@routes.get("/state")
async def get_state(request: web.Request) -> web.Response:
    state = request.config_dict[STATE]
    return json_response(
        {
            "bot": state.bot,
            "guilds": [
                {
                    "id": guild.id,
                    "name": guild.name,
                    "channels": [{"id": c["id"], "name": c["name"]} for c in guild.channels],
                    "member_count": len(guild.members),
                }
                for guild in state.guilds.values()
            ],
            "sessions": [
                {"id": session.id, "intents": session.intents}
                for session in state.sessions.values()
            ],
        }
    )


def create_control_app() -> web.Application:
    control = web.Application()
    control.add_routes(routes)
    return control
