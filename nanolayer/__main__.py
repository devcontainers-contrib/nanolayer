import os

import typer

from nanolayer.cli.install import app as install_app
from nanolayer.utils.analytics import setup_analytics
from nanolayer.utils.settings import NanolayerSettings
from nanolayer.utils.version import (
    resolve_own_package_version,
    resolve_own_release_version,
)

if "__file__" not in globals():
    # typer exception handling using __file__ which is
    # not available when running in pyoxidizer binary mode
    os.environ["_TYPER_STANDARD_TRACEBACK"] = "1"

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)
app.add_typer(install_app, name="install")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(resolve_own_package_version())
        raise typer.Exit()


def release_version_callback(value: bool) -> None:
    if value:
        typer.echo(resolve_own_release_version())
        raise typer.Exit()


@app.callback()
def version(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
    release_version: bool = typer.Option(
        None, "--release-version", callback=release_version_callback, is_eager=True
    ),
):
    if NanolayerSettings().enable_analytics:
        setup_analytics()

    return


def main() -> None:
    app()


if __name__ == "__main__":
    main()
