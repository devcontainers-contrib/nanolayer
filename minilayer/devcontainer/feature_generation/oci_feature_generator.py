from typing import Optional

from easyfs import Directory

from minilayer.devcontainer.feature_generation.dir_models.src_dir import SrcDir
from minilayer.devcontainer.feature_generation.dir_models.test_dir import TestDir
from minilayer.devcontainer.models.devcontainer_feature_definition import (
    FeatureDefinition,
)


class OCIFeatureGenerator:
    @staticmethod
    def generate(
        feature_definition: str, output_dir: str, release_version: Optional[str] = None
    ) -> None:
        definition_model = FeatureDefinition.parse_file(feature_definition)
        # create virtual file systm directory using easyfs
        virtual_dir = Directory()
        virtual_dir["src"] = SrcDir.from_definition_model(
            definition_model=definition_model, release_version=release_version
        )
        virtual_dir["test"] = TestDir.from_definition_model(
            definition_model=definition_model
        )

        # manifesting the virtual directory into local filesystem
        virtual_dir.create(output_dir)
