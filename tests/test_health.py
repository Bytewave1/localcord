from localcord import __version__
from localcord.app import create_app


async def test_health(aiohttp_client):
    client = await aiohttp_client(create_app())
    resp = await client.get("/_control/health")
    assert resp.status == 200
    assert await resp.json() == {"status": "ok", "version": __version__}
