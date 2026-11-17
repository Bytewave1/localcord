"""The gateway: the WebSocket a bot keeps open to receive events."""

from __future__ import annotations

import json
import secrets
import zlib
from typing import Any

from aiohttp import WSMsgType, web

from .keys import STATE
from .state import State

GATEWAY_PATH = "/gateway"
HEARTBEAT_INTERVAL_MS = 41250

# Opcodes
OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_PRESENCE_UPDATE = 3
OP_VOICE_STATE_UPDATE = 4
OP_RESUME = 6
OP_REQUEST_GUILD_MEMBERS = 8
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

# Close codes
CLOSE_UNKNOWN_OPCODE = 4001
CLOSE_DECODE_ERROR = 4002
CLOSE_NOT_AUTHENTICATED = 4003
CLOSE_ALREADY_AUTHENTICATED = 4005


class Session:
    """One connected bot."""

    def __init__(self, ws: web.WebSocketResponse, *, compress: bool) -> None:
        self.id = secrets.token_hex(16)
        self.ws = ws
        self.seq = 0
        self.identified = False
        self.intents = 0
        # zlib-stream shares one compression context across the whole connection.
        self._deflate = zlib.compressobj() if compress else None

    async def send(self, op: int, d: Any, *, t: str | None = None, s: int | None = None) -> None:
        payload = json.dumps({"op": op, "d": d, "s": s, "t": t})
        if self._deflate is None:
            await self.ws.send_str(payload)
        else:
            data = self._deflate.compress(payload.encode()) + self._deflate.flush(zlib.Z_SYNC_FLUSH)
            await self.ws.send_bytes(data)

    async def dispatch(self, event: str, data: Any) -> None:
        self.seq += 1
        await self.send(OP_DISPATCH, data, t=event, s=self.seq)


def gateway_url(request: web.Request) -> str:
    scheme = "wss" if request.secure else "ws"
    return f"{scheme}://{request.host}{GATEWAY_PATH}"


async def gateway_handler(request: web.Request) -> web.StreamResponse:
    if request.query.get("encoding", "json") != "json":
        raise web.HTTPBadRequest(text="localcord only supports encoding=json")

    state = request.app[STATE]
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    session = Session(ws, compress=request.query.get("compress") == "zlib-stream")
    await session.send(OP_HELLO, {"heartbeat_interval": HEARTBEAT_INTERVAL_MS})

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                await ws.close(code=CLOSE_DECODE_ERROR, message=b"Decode error")
                break
            try:
                payload = json.loads(msg.data)
                op, data = payload["op"], payload.get("d")
            except (ValueError, KeyError, TypeError):
                await ws.close(code=CLOSE_DECODE_ERROR, message=b"Decode error")
                break
            await _handle(state, session, request, op, data)
            if ws.closed:
                break
    finally:
        state.sessions.pop(session.id, None)
    return ws


async def _handle(state: State, session: Session, request: web.Request, op: int, data: Any) -> None:
    ws = session.ws

    if op == OP_HEARTBEAT:
        await session.send(OP_HEARTBEAT_ACK, None)

    elif op == OP_IDENTIFY:
        if session.identified:
            await ws.close(code=CLOSE_ALREADY_AUTHENTICATED, message=b"Already authenticated")
            return
        if not isinstance(data, dict) or "token" not in data:
            await ws.close(code=CLOSE_DECODE_ERROR, message=b"Decode error")
            return
        await _identify(state, session, request, data)

    elif op == OP_RESUME:
        # Sessions are not resumable yet: tell the bot to identify again.
        await session.send(OP_INVALID_SESSION, False)

    elif not session.identified:
        await ws.close(code=CLOSE_NOT_AUTHENTICATED, message=b"Not authenticated")

    elif op == OP_REQUEST_GUILD_MEMBERS:
        await _request_guild_members(state, session, data or {})

    elif op in (OP_PRESENCE_UPDATE, OP_VOICE_STATE_UPDATE):
        pass  # accepted and ignored for now

    else:
        await ws.close(code=CLOSE_UNKNOWN_OPCODE, message=b"Unknown opcode")


async def _identify(
    state: State, session: Session, request: web.Request, data: dict[str, Any]
) -> None:
    session.identified = True
    session.intents = int(data.get("intents", 0))
    state.sessions[session.id] = session

    ready = {
        "v": 10,
        "user": {**state.bot, "verified": True, "mfa_enabled": False, "email": None},
        "guilds": [{"id": guild_id, "unavailable": True} for guild_id in state.guilds],
        "session_id": session.id,
        "resume_gateway_url": gateway_url(request),
        "application": {"id": state.application["id"], "flags": state.application["flags"]},
    }
    if "shard" in data:
        ready["shard"] = data["shard"]
    await session.dispatch("READY", ready)

    for guild in state.guilds.values():
        await session.dispatch(
            "GUILD_CREATE", guild.payload(bot_id=state.bot["id"], intents=session.intents)
        )


async def _request_guild_members(state: State, session: Session, data: dict[str, Any]) -> None:
    guild = state.guilds.get(str(data.get("guild_id")))
    if guild is None:
        return
    members = guild.members
    user_ids = data.get("user_ids")
    if user_ids is not None:
        wanted = {user_ids} if isinstance(user_ids, str) else set(user_ids)
        members = [m for m in members if m["user"]["id"] in wanted]
    elif data.get("query"):
        prefix = data["query"].lower()
        members = [m for m in members if m["user"]["username"].lower().startswith(prefix)]
    limit = data.get("limit") or 0
    if limit:
        members = members[:limit]

    chunk = {
        "guild_id": guild.id,
        "members": members,
        "chunk_index": 0,
        "chunk_count": 1,
    }
    if "nonce" in data:
        chunk["nonce"] = data["nonce"]
    await session.dispatch("GUILD_MEMBERS_CHUNK", chunk)
