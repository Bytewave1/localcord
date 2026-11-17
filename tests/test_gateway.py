import json
import zlib

import pytest

from localcord.app import create_app
from localcord.gateway import HEARTBEAT_INTERVAL_MS

INTENT_GUILD_MEMBERS = 1 << 1


@pytest.fixture
async def client(aiohttp_client):
    return await aiohttp_client(create_app())


async def identify(ws, intents=0):
    await ws.send_json({"op": 2, "d": {"token": "t", "intents": intents, "properties": {}}})
    ready = await ws.receive_json()
    guild = await ws.receive_json()
    return ready, guild


async def test_hello_comes_first(client):
    ws = await client.ws_connect("/gateway?v=10&encoding=json")
    hello = await ws.receive_json()
    assert hello["op"] == 10
    assert hello["d"]["heartbeat_interval"] == HEARTBEAT_INTERVAL_MS


async def test_identify_gets_ready_then_guild_create(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    ready, guild = await identify(ws)

    assert (ready["op"], ready["t"], ready["s"]) == (0, "READY", 1)
    assert ready["d"]["user"]["bot"] is True
    assert ready["d"]["guilds"] == [{"id": guild["d"]["id"], "unavailable": True}]

    assert (guild["t"], guild["s"]) == ("GUILD_CREATE", 2)
    assert guild["d"]["name"] == "localcord"
    assert [c["name"] for c in guild["d"]["channels"]] == ["general"]


async def test_members_are_limited_without_the_members_intent(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    ready, guild = await identify(ws, intents=0)
    assert [m["user"]["id"] for m in guild["d"]["members"]] == [ready["d"]["user"]["id"]]
    assert guild["d"]["member_count"] == 2


async def test_members_intent_includes_everyone(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    _, guild = await identify(ws, intents=INTENT_GUILD_MEMBERS)
    assert len(guild["d"]["members"]) == 2


async def test_heartbeat_is_acked(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await ws.send_json({"op": 1, "d": None})
    assert (await ws.receive_json())["op"] == 11


async def test_request_guild_members(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    _, guild = await identify(ws)
    await ws.send_json(
        {"op": 8, "d": {"guild_id": guild["d"]["id"], "query": "", "limit": 0, "nonce": "abc"}}
    )
    chunk = await ws.receive_json()
    assert chunk["t"] == "GUILD_MEMBERS_CHUNK"
    assert chunk["d"]["nonce"] == "abc"
    assert len(chunk["d"]["members"]) == 2


async def test_resume_is_rejected(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await ws.send_json({"op": 6, "d": {"token": "t", "session_id": "x", "seq": 1}})
    assert await ws.receive_json() == {"op": 9, "d": False, "s": None, "t": None}


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ('{"op": 3, "d": {}}', 4003),  # anything but identify before identifying
        ('{"op": 99, "d": {}}', 4003),
        ("not json", 4002),
    ],
)
async def test_bad_first_message_closes(client, message, code):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await ws.send_str(message)
    await ws.receive()
    assert ws.close_code == code


async def test_identifying_twice_closes(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await identify(ws)
    await ws.send_json({"op": 2, "d": {"token": "t", "intents": 0}})
    await ws.receive()
    assert ws.close_code == 4005


async def test_unknown_opcode_after_identify_closes(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await identify(ws)
    await ws.send_json({"op": 99, "d": {}})
    await ws.receive()
    assert ws.close_code == 4001


async def test_zlib_stream(client):
    ws = await client.ws_connect("/gateway?compress=zlib-stream")
    inflate = zlib.decompressobj()
    msg = await ws.receive_bytes()
    assert msg.endswith(b"\x00\x00\xff\xff")
    assert json.loads(inflate.decompress(msg))["op"] == 10

    await ws.send_json({"op": 1, "d": None})
    assert json.loads(inflate.decompress(await ws.receive_bytes()))["op"] == 11


async def test_session_is_listed_while_connected(client):
    ws = await client.ws_connect("/gateway")
    await ws.receive_json()
    await identify(ws, intents=513)

    sessions = (await (await client.get("/_control/state")).json())["sessions"]
    assert [s["intents"] for s in sessions] == [513]

    await ws.close()
    for _ in range(50):
        sessions = (await (await client.get("/_control/state")).json())["sessions"]
        if not sessions:
            break
    assert sessions == []
