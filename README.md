# localcord

A local Discord API emulator. Point your bot at it instead of discord.com and
test it offline: no token, no test server, no rate limits.

It runs as a standalone server, so it works with any library that lets you
change the API address.

> **Status: early development.** A bot can log in and come online: it receives
> `READY` and one guild with a `#general` channel. Sending messages and slash
> commands are not emulated yet. See the roadmap.

## Install

localcord is not on PyPI yet. Install from source:

```
git clone https://github.com/Bytewave1/localcord
cd localcord
pip install -e .
```

## Start the server

```
localcord start
```

It listens on `http://127.0.0.1:8787`. Use `--port` to change that.

## Connect a bot

Any string works as the token.

### discord.py

discord.py has no option for the API address, so localcord ships a helper that
sets it. Call it before you create the client:

```python
import discord
import localcord.discordpy

localcord.discordpy.use("http://127.0.0.1:8787")

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"online as {client.user} in {[g.name for g in client.guilds]}")

client.run("any-token-works")
```

### discord.js

```js
const { Client, GatewayIntentBits } = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds],
  rest: { api: 'http://127.0.0.1:8787/api' },
});

client.once('ready', (c) => console.log(`online as ${c.user.tag}`));
client.login('any-token-works');
```

### Other libraries

Set the REST base URL to `http://127.0.0.1:8787/api/v10`. The gateway address
is returned by `GET /gateway/bot`, or use `ws://127.0.0.1:8787/gateway` directly.

## What is emulated

| Area | Supported |
|---|---|
| REST | `GET /gateway`, `GET /gateway/bot`, `GET /users/@me`, `GET /oauth2/applications/@me` |
| Gateway | HELLO, IDENTIFY, READY, GUILD_CREATE, heartbeat, REQUEST_GUILD_MEMBERS, `zlib-stream` compression |
| Intents | Without `GUILD_MEMBERS`, a guild only lists the bot's own member, as on Discord |

Routes that are not implemented answer `501` with a message that names the
route, so you can tell a gap in localcord from a bug in your bot. RESUME is
answered with "invalid session", which makes the library identify again.

Tested against discord.py 2.7 and discord.js 14.

## Control API

Routes under `/_control` do not exist on Discord. They are how tests inspect
the emulator.

| Route | Returns |
|---|---|
| `GET /_control/health` | Server status and version |
| `GET /_control/state` | The bot user, guilds, channels and connected sessions |

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| M0 | Project skeleton, CI | Done |
| M1 | Gateway handshake; discord.py and discord.js bots come online | Done |
| M2 | Messages in both directions, control API to send as a user | Next |
| M3 | Slash commands: register, invoke, respond, follow up | |
| M4 | pytest plugin, Docker image, first PyPI release | |

## Development

```
pip install -e ".[dev]"
ruff check .
pytest
```

The test suite starts a real discord.py client against the emulator.

## License

MIT. localcord is not affiliated with or endorsed by Discord Inc.
