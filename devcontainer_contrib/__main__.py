import typer
from devcontainer_contrib.cli.features import app as feature_app

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)
app.add_typer(feature_app, name="features")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
