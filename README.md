# localcord

A local Discord API emulator. Point your bot at it instead of discord.com and
test it offline: no token, no test server, no rate limits.

It runs as a standalone server, so it works with any library that lets you
change the API address (discord.py, discord.js, and others).

> **Status: early development.** The server starts and answers a health check.
> It does not emulate Discord yet. See the roadmap for what comes next.

## Install

```
pip install localcord
```

Until the first release is on PyPI, install from source:

```
git clone https://github.com/Bytewave1/localcord
cd localcord
pip install -e ".[dev]"
```

## Usage

```
localcord start
```

The server listens on `http://127.0.0.1:8787`. Check that it is up:

```
curl http://127.0.0.1:8787/_control/health
```

## Roadmap

| Stage | Scope | Done when |
|---|---|---|
| M0 | Project skeleton, CI | Tests run on every push |
| M1 | Gateway handshake: `GET /gateway/bot`, HELLO, IDENTIFY, READY, heartbeat | A discord.py bot and a discord.js bot come online |
| M2 | Messages in both directions, control API | A ping-pong test passes without a token |
| M3 | Slash commands: register, invoke, respond, follow up | `/ping` is triggered and asserted in a test |
| M4 | pytest plugin, Docker image, first PyPI release | A stranger gets it running in two minutes |

## Development

```
pip install -e ".[dev]"
ruff check .
pytest
```

## License

MIT. localcord is not affiliated with or endorsed by Discord Inc.
