import typer

from nanolayer.cli.install import app as install_app
from nanolayer.utils.version import (
    resolve_own_package_version,
    resolve_own_release_version,
)

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
    return


def main() -> None:
    app()


if __name__ == "__main__":
    main()
