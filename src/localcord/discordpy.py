"""Point discord.py at a localcord server.

discord.py has no public option for the API address, so this sets the two
class attributes it reads them from. Call it before creating your client:

    import localcord.discordpy
    localcord.discordpy.use("http://127.0.0.1:8787")
"""

from __future__ import annotations

DEFAULT_URL = "http://127.0.0.1:8787"


def use(base_url: str = DEFAULT_URL) -> None:
    import yarl
    from discord import gateway, http

    base = yarl.URL(base_url.rstrip("/"))
    http.Route.BASE = f"{base}/api/v10"
    gateway.DiscordWebSocket.DEFAULT_GATEWAY = base.with_scheme(
        "wss" if base.scheme == "https" else "ws"
    ).with_path("/gateway")
