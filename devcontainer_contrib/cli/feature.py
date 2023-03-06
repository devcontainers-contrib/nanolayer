import typer
import logging
import pathlib
from typing import List, Optional
import json
from devcontainer_contrib.cli.download.download_feature import download_feature
from devcontainer_contrib.cli.inspect.extract_devcontainer_feature_obj import extract_devcontainer_feature_obj

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)

app.command()

@app.command("generate")
def generate(
    feature_definition: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:
    try:
        from devcontainer_contrib.cli.generate.generate_feature import generate
    except ImportError as e:
        logger.error("Some imports required for feature generation are missing.\nMake sure you have included the generate extras during installation.\n eg. 'pip install devcontainer-contrib[generate]'")
        raise typer.Exit(code=1) from e

    generate(feature_definition, output_dir)



def _validate_args(value: List[str]):
    for arg in value:
        splitted_arg = arg.split("=")
        if len(splitted_arg) != 2 or len(splitted_arg[0]) == 0:
            raise typer.BadParameter("Must be formatted as 'key=value'")
    return value


@app.command("download")
def download(
    feature: str,
) -> None:
    download_location = download_feature(feature)

    print(f"feature downloaded to {download_location}")


@app.command("inspect")
def inspect(
    feature: str,
) -> None:
    devcontainer_feature_obj = extract_devcontainer_feature_obj(feature)

    print(json.dumps(devcontainer_feature_obj, indent=4))


