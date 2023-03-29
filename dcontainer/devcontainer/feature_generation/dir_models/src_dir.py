from typing import Optional

from easyfs import Directory

from dcontainer.devcontainer.feature_generation.file_models.library_scripts_sh import (
    LibraryScriptsSH,
)
from dcontainer.devcontainer.feature_generation.file_models.devcontainer_feature_json import (
    DevcontainerFeatureJson,
)

from dcontainer.devcontainer.feature_generation.file_models.install_sh import InstallSH
from dcontainer.devcontainer.models.devcontainer_feature_definition import (
    FeatureDefinition,
)


class SrcDir(Directory):
    @classmethod
    def from_definition_model(
        cls, definition_model: FeatureDefinition, release_version: Optional[str] = None
    ) -> "Directory":
        feature_id = definition_model.id

        virtual_dir = {}

        virtual_dir[f"{feature_id}/library_scripts.sh"] = LibraryScriptsSH(
           release_version=release_version,
        )

        virtual_dir[f"{feature_id}/install.sh"] = InstallSH(install_command=definition_model.install_command,
                                                            options=definition_model.options,
                                                            dependencies=definition_model.dependencies)
        virtual_dir[
            f"{feature_id}/devcontainer-feature.json"
        ] = DevcontainerFeatureJson(definition_model)

        return cls(dictionary=virtual_dir)
