"""Runs a real discord.py client against the emulator."""

import asyncio

import pytest

from localcord.app import create_app

discord = pytest.importorskip("discord")

import localcord.discordpy  # noqa: E402


@pytest.fixture
async def server(aiohttp_server, monkeypatch):
    server = await aiohttp_server(create_app())
    # Restore discord.py's real addresses after the test.
    monkeypatch.setattr(discord.http.Route, "BASE", discord.http.Route.BASE)
    monkeypatch.setattr(
        discord.gateway.DiscordWebSocket,
        "DEFAULT_GATEWAY",
        discord.gateway.DiscordWebSocket.DEFAULT_GATEWAY,
    )
    localcord.discordpy.use(f"http://{server.host}:{server.port}")
    return server


async def run_until_ready(client):
    await client.login("any-token-works")
    task = asyncio.create_task(client.connect(reconnect=False))
    await asyncio.wait_for(client.wait_until_ready(), timeout=10)
    return task


async def test_client_comes_online(server):
    client = discord.Client(intents=discord.Intents.default())
    task = await run_until_ready(client)
    try:
        assert client.user.name == "localcord-bot"
        assert client.user.bot
        assert [g.name for g in client.guilds] == ["localcord"]
        guild = client.guilds[0]
        assert [c.name for c in guild.text_channels] == ["general"]
        assert guild.me.id == client.user.id
        assert guild.member_count == 2
    finally:
        await client.close()
        await task


async def test_members_intent_fills_the_member_cache(server):
    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)
    task = await run_until_ready(client)
    try:
        names = sorted(m.name for m in client.guilds[0].members)
        assert names == ["localcord-bot", "owner"]
    finally:
        await client.close()
        await task
