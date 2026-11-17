"""Discord-style snowflake IDs."""

import itertools
import time

DISCORD_EPOCH_MS = 1420070400000

_increment = itertools.count()


def new_snowflake() -> str:
    """Return a new unique ID in Discord's snowflake format, as a string."""
    ms = int(time.time() * 1000) - DISCORD_EPOCH_MS
    return str((ms << 22) | (next(_increment) & 0xFFF))
