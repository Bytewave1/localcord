"""Command line entry point: `localcord start`."""

import argparse

from aiohttp import web

from . import __version__
from .app import create_app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="localcord", description=__doc__)
    parser.add_argument("--version", action="version", version=f"localcord {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="start the emulator")
    start.add_argument("--host", default=DEFAULT_HOST)
    start.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "start":
        web.run_app(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
