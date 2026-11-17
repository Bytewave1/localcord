"""In-memory world the emulator serves: the bot, its application and its guilds.

Entities are stored as plain dicts in the shape Discord sends them over the API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .snowflake import new_snowflake

if TYPE_CHECKING:
    from .gateway import Session

INTENT_GUILD_MEMBERS = 1 << 1

# What a fresh @everyone role allows: view channels, send messages, embed links,
# attach files, read history, add reactions, connect, speak, use slash commands.
DEFAULT_PERMISSIONS = str(
    (1 << 6) | (1 << 10) | (1 << 11) | (1 << 14) | (1 << 15)
    | (1 << 16) | (1 << 20) | (1 << 21) | (1 << 31)
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_user(username: str, *, bot: bool = False) -> dict[str, Any]:
    return {
        "id": new_snowflake(),
        "username": username,
        "discriminator": "0",
        "global_name": None,
        "avatar": None,
        "bot": bot,
        "system": False,
        "flags": 0,
        "public_flags": 0,
    }


def make_member(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "user": user,
        "nick": None,
        "avatar": None,
        "roles": [],
        "joined_at": _now(),
        "premium_since": None,
        "deaf": False,
        "mute": False,
        "flags": 0,
        "pending": False,
    }


def make_text_channel(guild_id: str, name: str, position: int = 0) -> dict[str, Any]:
    return {
        "id": new_snowflake(),
        "type": 0,
        "guild_id": guild_id,
        "position": position,
        "permission_overwrites": [],
        "name": name,
        "topic": None,
        "nsfw": False,
        "last_message_id": None,
        "rate_limit_per_user": 0,
        "parent_id": None,
        "flags": 0,
    }


@dataclass
class Guild:
    id: str
    name: str
    owner_id: str
    roles: list[dict[str, Any]] = field(default_factory=list)
    channels: list[dict[str, Any]] = field(default_factory=list)
    members: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_now)

    def payload(self, *, bot_id: str, intents: int) -> dict[str, Any]:
        """The GUILD_CREATE payload. Without the members intent, Discord only
        includes the bot's own member, so we do the same."""
        if intents & INTENT_GUILD_MEMBERS:
            members = self.members
        else:
            members = [m for m in self.members if m["user"]["id"] == bot_id]
        return {
            "id": self.id,
            "name": self.name,
            "icon": None,
            "splash": None,
            "discovery_splash": None,
            "owner_id": self.owner_id,
            "afk_channel_id": None,
            "afk_timeout": 300,
            "verification_level": 0,
            "default_message_notifications": 0,
            "explicit_content_filter": 0,
            "roles": self.roles,
            "emojis": [],
            "stickers": [],
            "features": [],
            "mfa_level": 0,
            "application_id": None,
            "system_channel_id": self.channels[0]["id"] if self.channels else None,
            "system_channel_flags": 0,
            "rules_channel_id": None,
            "public_updates_channel_id": None,
            "safety_alerts_channel_id": None,
            "max_members": 500000,
            "vanity_url_code": None,
            "description": None,
            "banner": None,
            "premium_tier": 0,
            "premium_subscription_count": 0,
            "premium_progress_bar_enabled": False,
            "preferred_locale": "en-US",
            "nsfw_level": 0,
            "joined_at": self.created_at,
            "large": False,
            "unavailable": False,
            "member_count": len(self.members),
            "members": members,
            "channels": self.channels,
            "threads": [],
            "voice_states": [],
            "presences": [],
            "stage_instances": [],
            "guild_scheduled_events": [],
            "soundboard_sounds": [],
        }


def make_guild(name: str, owner: dict[str, Any], bot: dict[str, Any]) -> Guild:
    guild_id = new_snowflake()
    everyone = {
        "id": guild_id,  # the @everyone role shares the guild's ID
        "name": "@everyone",
        "color": 0,
        "hoist": False,
        "icon": None,
        "unicode_emoji": None,
        "position": 0,
        "permissions": DEFAULT_PERMISSIONS,
        "managed": False,
        "mentionable": False,
        "flags": 0,
    }
    return Guild(
        id=guild_id,
        name=name,
        owner_id=owner["id"],
        roles=[everyone],
        channels=[make_text_channel(guild_id, "general")],
        members=[make_member(owner), make_member(bot)],
    )


@dataclass
class State:
    bot: dict[str, Any]
    owner: dict[str, Any]
    guilds: dict[str, Guild]
    sessions: dict[str, Session] = field(default_factory=dict)

    @classmethod
    def default(cls) -> State:
        """One guild with a #general channel, an owner, and the bot."""
        bot = make_user("localcord-bot", bot=True)
        owner = make_user("owner")
        guild = make_guild("localcord", owner, bot)
        return cls(bot=bot, owner=owner, guilds={guild.id: guild})

    @property
    def application(self) -> dict[str, Any]:
        return {
            "id": self.bot["id"],  # bot user and application share an ID
            "name": self.bot["username"],
            "icon": None,
            "description": "",
            "summary": "",
            "bot_public": True,
            "bot_require_code_grant": False,
            "verify_key": "",
            "flags": 0,
            "owner": self.owner,
            "team": None,
        }
