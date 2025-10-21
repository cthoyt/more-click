"""Utilities for web applications."""

from __future__ import annotations

import importlib
import sys
import warnings
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

import click

from .options import (
    Server,
    flask_debug_option,
    gunicorn_timeout_option,
    server_option,
    verbose_option,
    with_gunicorn_option,
    workers_option,
)

if TYPE_CHECKING:
    import flask
    import gunicorn.app.base

__all__ = [
    "make_gunicorn_app",
    "make_web_command",
    "run_app",
]


def make_web_command(  # noqa:C901
    app: str | flask.Flask | Callable[[], flask.Flask],
    *,
    group: click.Group | None = None,
    command_kwargs: Mapping[str, Any] | None = None,
    default_port: None | str | int = None,
    default_host: str | None = None,
) -> click.Command:
    """Make a command for running a web application."""
    group_decorator: Callable[[Any], click.Command]
    if group is None:
        group_decorator = click.command(**(command_kwargs or {}))
    else:
        group_decorator = group.command(**(command_kwargs or {}))

    if isinstance(default_port, str):
        default_port = int(default_port)

    @group_decorator  # type:ignore
    @click.option(
        "--host",
        type=str,
        default=default_host or "0.0.0.0",  # noqa:S104
        help="Flask host.",
        show_default=True,
    )
    @click.option(
        "--port",
        type=int,
        default=default_port or 5000,
        help="Flask port.",
        show_default=True,
    )
    @with_gunicorn_option
    @server_option
    @workers_option
    @verbose_option
    @gunicorn_timeout_option
    @flask_debug_option
    def web(
        host: str,
        port: str,
        with_gunicorn: bool,
        server: Server,
        workers: int,
        debug: bool,
        timeout: int | None,
    ) -> None:
        """Run the web application."""
        import flask

        nonlocal app
        if isinstance(app, str):
            if app.count(":") != 1:
                raise ValueError(
                    "there should be exactly one colon in the string pointing to"
                    " an app like modulename.submodulename:appname_in_module"
                )
            package_name, class_name = app.split(":", 1)
            package = importlib.import_module(package_name)
            app = getattr(package, class_name)
            if isinstance(app, flask.Flask):
                pass
            elif callable(app):
                app = app()
            else:
                raise TypeError(
                    "when using a string path with more_click.make_web_command(),"
                    " it's required that it points to either an instance of a Flask"
                    " application or a 0-argument function that returns one."
                )
        elif isinstance(app, flask.Flask):
            pass
        elif callable(app):
            app = app()
        else:
            raise TypeError(
                "when using more_click.make_web_command(), the app argument should either"
                " be an instance of a Flask app, a 0-argument function that returns a Flask app,"
                " a string pointing to a Flask app in a python module, or a string pointing to a"
                " 0-argument function that returns a Flask app"
            )

        if debug and with_gunicorn:
            click.secho("can not use --debug and --with-gunicorn together")
            raise sys.exit(1)

        run_app(
            app=app,
            host=host,
            port=port,
            workers=workers,
            with_gunicorn=with_gunicorn,
            server=server,
            debug=debug,
            timeout=timeout,
        )

    return web


def run_app(
    app: flask.Flask,
    with_gunicorn: bool,
    server: Server | None = None,
    host: str | None = None,
    port: str | None = None,
    workers: int | None = None,
    timeout: int | None = None,
    debug: bool = False,
) -> None:
    """Run the application."""
    if with_gunicorn:
        warnings.warn("use `server` option to explicitly specify `gunicorn`", stacklevel=2)
        server = "gunicorn"

    if server == "flask" or server is None:
        app.run(host=host, port=port, debug=debug)
    elif server == "gunicorn":
        if host is None or port is None or workers is None:
            raise ValueError("must specify host, port, and workers for gunicorn.")
        if debug:
            raise ValueError("can not use debug with gunicorn")
        gunicorn_app = make_gunicorn_app(
            app,
            host=host,
            port=port,
            workers=workers,
            timeout=timeout,
        )
        gunicorn_app.run()
    elif server == "uvicorn":
        raise NotImplementedError
    elif server == "hypercorn":
        if host is None or port is None:
            raise ValueError("must specify host and port for hypercorn.")

        import asyncio

        from hypercorn.asyncio import serve
        from hypercorn.config import Config

        config = Config()
        config.bind = f"{host}:{port}"
        asyncio.run(serve(app, config))
    else:
        raise ValueError(f"invalid server: {server}")


def make_gunicorn_app(
    app: flask.Flask,
    host: str,
    port: str,
    workers: int,
    timeout: int | None = None,
    **kwargs: Any,
) -> gunicorn.app.base.BaseApplication:
    """Make a GUnicorn App."""
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        """A standalone application adapter."""

        def __init__(self, options: dict[str, Any] | None = None) -> None:
            """Initialize the standalone applicaton object."""
            self.options = options or {}
            self.application = app
            super().__init__()

        def init(self, parser: Any, opts: Any, args: Any) -> None:
            """Initialize the app."""

        def load_config(self) -> None:
            """Load the configuration."""
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self) -> flask.Flask:
            """Load the app."""
            return self.application

    kwargs.update(
        {
            "bind": f"{host}:{port}",
            "workers": workers,
        }
    )
    if timeout is not None:
        kwargs["timeout"] = timeout

    return StandaloneApplication(kwargs)
