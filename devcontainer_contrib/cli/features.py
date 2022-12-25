import typer
from unittest import mock
from pydantic import Extra
import pathlib
from devcontainer_contrib.models.devcontainer_feature_definition import (
    FeatureDefinition,
)
from devcontainer_contrib.models.devcontainer_feature import Feature
from enum import Enum
from devcontainer_contrib.features.dependencies_sh import (
    DependenciesSH,
)
from devcontainer_contrib.features.install_command_sh import (
    InstallCommandSH,
)
from devcontainer_contrib.features.install_sh import InstallSH
from devcontainer_contrib.features.test_sh import TestSH
from easyfs import Directory, File

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)


class OutputType(Enum):
    feature_dir: str = "feature_dir"
    dependencies: str = "dependencies"
    test: str = "test"


@app.command("generate")
def generate(
    feature_definition: pathlib.Path,
    output_dir: pathlib.Path,
    output_type: OutputType = typer.Option(OutputType.feature_dir),
) -> None:

    definition_model = FeatureDefinition.parse_file(feature_definition)
    feature_id = definition_model.id
    virtual_dir = Directory()

    if output_type == OutputType.dependencies:
        dependencies_sh = DependenciesSH(definition_model.dependencies, definition_model.options).to_str()

        # create virtual file systm directory using easyfs
        virtual_dir["dependencies.sh"] = File(dependencies_sh.encode())

        # manifesting the virtual directory into local filesystem
        virtual_dir.create(output_dir.as_posix())

    elif output_type == OutputType.test:
        test_sh = TestSH(definition_model.test_command or "").to_str()
        
        # create virtual file systm directory using easyfs
        virtual_dir["test.sh"] = File(test_sh.encode())

        # manifesting the virtual directory into local filesystem
        virtual_dir.create(output_dir.as_posix())

    elif output_type == OutputType.feature_dir:
        # create files as strings
        feature_json = definition_model.to_feature_model().json(indent=4, exclude_none=True)
        test_sh = TestSH(definition_model.test_command or "").to_str()
        install_command_sh = InstallCommandSH(definition_model.install_command or "").to_str()
        dependencies_sh = DependenciesSH(definition_model.dependencies, definition_model.options).to_str()
        install_sh = InstallSH().to_str()

        # create virtual file systm directory using easyfs
        virtual_dir[f"src/{feature_id}/dependencies.sh"] = File(dependencies_sh.encode())
        virtual_dir[f"src/{feature_id}/install_command.sh"] = File(install_command_sh.encode())
        virtual_dir[f"src/{feature_id}/install.sh"] = File(install_sh.encode())
        virtual_dir[f"src/{feature_id}/devcontainer-feature.json"] = File(feature_json.encode())
        virtual_dir[f"test/{feature_id}/test.sh"] = File(test_sh.encode())
        
        # manifesting the virtual directory into local filesystem
        virtual_dir.create(output_dir.as_posix())

    else:
        raise ValueError(f"invalid output type: {output_type}")
