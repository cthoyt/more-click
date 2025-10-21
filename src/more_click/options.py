"""More click options."""

from __future__ import annotations

import logging
import multiprocessing
import typing
from collections.abc import Callable
from typing import Any, Literal, TypeAlias

import click

__all__ = [
    "debug_option",
    "flask_debug_option",
    "force_option",
    "gunicorn_timeout_option",
    "host_option",
    "log_level_option",
    "port_option",
    "server_option",
    "verbose_option",
    "with_gunicorn_option",
    "workers_option",
]

from click.decorators import FC

LOG_FMT = "%(asctime)s %(levelname)-8s %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _debug_callback(_ctx: click.Context, _param: Any, value: int) -> None:
    if not value:
        logging.basicConfig(level=logging.WARNING, format=LOG_FMT, datefmt=LOG_DATEFMT)
    elif value == 1:
        logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=LOG_DATEFMT)
    else:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FMT, datefmt=LOG_DATEFMT)


verbose_option = click.option(
    "-v",
    "--verbose",
    count=True,
    callback=_debug_callback,
    expose_value=False,
    help="Enable verbose mode. More -v's means more verbose.",
)


def _number_of_workers() -> int:
    """Calculate the default number of workers."""
    return (multiprocessing.cpu_count() * 2) + 1


Server: TypeAlias = Literal["flask", "hypercorn", "uvicorn", "gunicorn"]

host_option = click.option(
    "--host",
    type=str,
    default="0.0.0.0",  # noqa:S104
    help="The host to serve to",
    show_default=True,
)
port_option = click.option(
    "--port", type=int, default=5000, help="The port to serve on", show_default=True
)
with_gunicorn_option = click.option(
    "--with-gunicorn", is_flag=True, help="Use gunicorn instead of flask dev server"
)
server_option = click.option(
    "--server",
    type=click.Choice(list(typing.get_args(Server))),
    default="flask",
    help="The server to use",
)
workers_option = click.option(
    "--workers",
    type=int,
    default=_number_of_workers(),
    show_default=True,
    help="Number of workers (e.g., when using gunicorn)",
)
force_option = click.option("-f", "--force", is_flag=True)
debug_option = click.option("--debug", is_flag=True)
flask_debug_option = click.option(
    "--debug",
    is_flag=True,
    help="Run flask dev server in debug mode (when not using --with-gunicorn)",
)
gunicorn_timeout_option = click.option("--timeout", type=int, help="The timeout used for gunicorn")

# sorted level names, by log-level
_level_names = sorted(logging._nameToLevel, key=logging._nameToLevel.get)  # type: ignore


def log_level_option(default: str | int = logging.INFO) -> Callable[[FC], FC]:
    """Create a click option to select a log-level by name."""
    # normalize default to be a string
    if isinstance(default, int):
        default = logging.getLevelName(level=default)

    return click.option(
        "-ll",
        "--log-level",
        type=click.Choice(choices=_level_names, case_sensitive=False),
        default=default,
    )
