import pathlib
from typing import Union, Optional

from easyfs import Directory

from dcontainer.cli.generate.dir_models.src_dir import SrcDir
from dcontainer.cli.generate.dir_models.test_dir import TestDir
from dcontainer.models.devcontainer_feature_definition import FeatureDefinition


def generate(
    feature_definition: str,
    output_dir: str,
    release_version: Optional[str] = None
) -> None:
    definition_model = FeatureDefinition.parse_file(feature_definition)
    # create virtual file systm directory using easyfs
    virtual_dir = Directory()
    virtual_dir["src"] = SrcDir.from_definition_model(definition_model=definition_model, release_version=release_version)
    virtual_dir["test"] = TestDir.from_definition_model(definition_model=definition_model)

    # manifesting the virtual directory into local filesystem
    virtual_dir.create(output_dir)
