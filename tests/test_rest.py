import pytest

from localcord.app import create_app

AUTH = {"Authorization": "Bot test-token"}


@pytest.fixture
async def client(aiohttp_client):
    return await aiohttp_client(create_app())


async def test_requires_token(client):
    resp = await client.get("/api/v10/users/@me")
    assert resp.status == 401
    assert (await resp.json())["message"] == "401: Unauthorized"


async def test_current_user_is_a_bot(client):
    resp = await client.get("/api/v10/users/@me", headers=AUTH)
    assert resp.status == 200
    user = await resp.json()
    assert user["bot"] is True
    assert user["username"] == "localcord-bot"


async def test_application_shares_the_bot_id(client):
    user = await (await client.get("/api/v10/users/@me", headers=AUTH)).json()
    resp = await client.get("/api/v10/oauth2/applications/@me", headers=AUTH)
    assert resp.status == 200
    assert (await resp.json())["id"] == user["id"]


async def test_gateway_bot_points_at_this_server(client):
    resp = await client.get("/api/v10/gateway/bot", headers=AUTH)
    data = await resp.json()
    assert data["url"] == f"ws://{client.host}:{client.port}/gateway"
    assert data["shards"] == 1


async def test_gateway_needs_no_token(client):
    resp = await client.get("/api/v10/gateway")
    assert resp.status == 200


@pytest.mark.parametrize("prefix", ["/api/v10", "/api/v9", "/api"])
async def test_api_prefixes(client, prefix):
    resp = await client.get(f"{prefix}/users/@me", headers=AUTH)
    assert resp.status == 200


async def test_unknown_route_says_so(client):
    resp = await client.get("/api/v10/guilds/1/bans", headers=AUTH)
    assert resp.status == 501
    assert "does not implement GET /api/v10/guilds/1/bans" in (await resp.json())["message"]


async def test_content_type_has_no_charset(client):
    # discord.py only parses the body as JSON when the header matches exactly.
    resp = await client.get("/api/v10/users/@me", headers=AUTH)
    assert resp.headers["Content-Type"] == "application/json"
