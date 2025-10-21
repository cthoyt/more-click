"""Command line interface for :mod:`more_click`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """CLI for more_click."""


if __name__ == "__main__":
    main()
