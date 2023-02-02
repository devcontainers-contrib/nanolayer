import typer

import pathlib
from devcontainer_contrib.models.devcontainer_feature_definition import (
    FeatureDefinition,
)

from devcontainer_contrib.features.dir_modules.test_dir import TestDir
from devcontainer_contrib.features.dir_modules.src_dir import SrcDir

from easyfs import Directory

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)


@app.command("generate")
def generate(
    feature_definition: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:

    definition_model = FeatureDefinition.parse_file(feature_definition)
    feature_id = definition_model.id
    # create virtual file systm directory using easyfs
    virtual_dir = Directory()
    virtual_dir[f"src"] = SrcDir.from_definition_model(definition_model)
    virtual_dir[f"test"] = TestDir.from_definition_model(definition_model)

    # manifesting the virtual directory into local filesystem
    virtual_dir.create(output_dir.as_posix())
