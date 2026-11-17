"""Typed keys for values stored on the aiohttp application."""

from aiohttp import web

from .state import State

STATE = web.AppKey("state", State)
