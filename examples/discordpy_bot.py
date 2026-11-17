"""Minimal discord.py bot that connects to a local localcord server.

Start the server first:  localcord start
Then run this file:      python examples/discordpy_bot.py
"""

import discord

import localcord.discordpy

localcord.discordpy.use("http://127.0.0.1:8787")

client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    guilds = ", ".join(guild.name for guild in client.guilds)
    print(f"online as {client.user} in: {guilds}")


client.run("any-token-works")
