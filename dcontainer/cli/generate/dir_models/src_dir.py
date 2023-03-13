from easyfs import Directory, File
from typing import Optional

from dcontainer.cli.generate.file_models.dependencies_sh import DependenciesSH
from dcontainer.cli.generate.file_models.devcontainer_feature_json import (
    DevcontainerFeatureJson,
)
from dcontainer.cli.generate.file_models.install_command_sh import InstallCommandSH
from dcontainer.cli.generate.file_models.install_sh import InstallSH
from dcontainer.models.devcontainer_feature_definition import FeatureDefinition


class SrcDir(Directory):
    @classmethod
    def from_definition_model(cls, definition_model: FeatureDefinition, release_version: Optional[str] = None) -> "Directory":
        feature_id = definition_model.id

        virtual_dir = {}
        virtual_dir[f"{feature_id}/dependencies.sh"] = DependenciesSH(
            definition_model.dependencies, definition_model.options, release_version
        )
        virtual_dir[f"{feature_id}/install_command.sh"] = InstallCommandSH(
            definition_model.install_command or ""
        )
        virtual_dir[f"{feature_id}/install.sh"] = InstallSH()
        virtual_dir[
            f"{feature_id}/devcontainer-feature.json"
        ] = DevcontainerFeatureJson(definition_model)

        return cls(dictionary=virtual_dir)
