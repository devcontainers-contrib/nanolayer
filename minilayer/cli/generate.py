import logging
import pathlib
from typing import Optional

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)

app.command()


@app.command("devcontainer-feature")
def generate_command(
    feature_definition: pathlib.Path,
    output_dir: pathlib.Path,
    release_version: Optional[str] = None,
) -> None:
    try:
        from minilayer.devcontainer.feature_generation.oci_feature_generator import (
            OCIFeatureGenerator,
        )
    except ImportError as e:
        logger.error(
            "Some imports required for feature generation are missing.\nMake sure you have included the generate extras during installation.\n eg. 'pip install minilayer[generate]'"
        )
        raise typer.Exit(code=1) from e

    OCIFeatureGenerator.generate(
        feature_definition=feature_definition.as_posix(),
        output_dir=output_dir.as_posix(),
        release_version=release_version,
    )
