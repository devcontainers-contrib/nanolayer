import json
import logging
import pathlib
from typing import List, Optional

import typer

from devcontainer_contrib.cli.download.download_feature import download_feature
from devcontainer_contrib.cli.inspect.extract_devcontainer_feature_dict import (
    extract_devcontainer_feature_dict,
)
from devcontainer_contrib.cli.install.install_feature import install_feature

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)

app.command()


@app.command("generate")
def generate_command(
    feature_definition: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:
    try:
        from devcontainer_contrib.cli.generate.generate_feature import generate
    except ImportError as e:
        logger.error(
            "Some imports required for feature generation are missing.\nMake sure you have included the generate extras during installation.\n eg. 'pip install devcontainer-contrib[generate]'"
        )
        raise typer.Exit(code=1) from e

    generate(feature_definition.as_posix(), output_dir.as_posix())


def _validate_args(value: Optional[List[str]]):
    if value is not None:
        for arg in value:
            splitted_arg = arg.split("=")
            if len(splitted_arg) < 2 or len(splitted_arg[0]) == 0:
                raise typer.BadParameter("Must be formatted as 'key=value'")
    return value


@app.command("download")
def download_command(
    feature: str,
) -> None:
    download_location = download_feature(feature)
    print(f"feature downloaded to {download_location}")


@app.command("inspect")
def inspect_command(
    feature: str,
) -> None:
    devcontainer_feature_dict = extract_devcontainer_feature_dict(feature)
    print(json.dumps(devcontainer_feature_dict, indent=4))


@app.command("install")
def install_command(
    feature: str,
    option: Optional[List[str]] = typer.Option(None, callback=_validate_args),
    verbose: bool = False
) -> None:
    def _strip_if_wrapped_around(value: str, char: str) -> str:
        if len(char) > 1:
            raise ValueError("For clarity sake, will only strip one character at a time")
        
        if value[0] == char and value[-1] == char:
            return value.strip(char)
        return value


    if option is None:
        options = []
    else:
        options = option
    
    options_dict = {}
    for single_option in options:
        single_option = _strip_if_wrapped_around(single_option, '"')

        option_name = single_option.split("=")[0]

        option_value = single_option[len(option_name)+1:]
        option_value = _strip_if_wrapped_around(option_value, '"')

        options_dict[option_name] = option_value

    install_feature(feature=feature, options=options_dict, verbose=verbose)
