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

    feature_definition_model = FeatureDefinition.parse_file(feature_definition)

    if output_type == OutputType.dependencies:

        dependencies_file = DependenciesSH(
            feature_definition_model.dependencies, feature_definition_model.options
        ).to_str()
        dir_obj = Directory()
        dir_obj["dependencies.sh"] = File(dependencies_file.encode())
        dir_obj.create(output_dir.as_posix())

    elif output_type == OutputType.test:
        test_file = TestSH(command=feature_definition_model.test_command or "").to_str()
        dir_obj = Directory()
        dir_obj["test.sh"] = File(test_file.encode())
        dir_obj.create(output_dir.as_posix())

    elif output_type == OutputType.feature_dir:
        with mock.patch.object(Feature.Config, "extra", Extra.ignore):
            feature_json_file = Feature(**feature_definition_model.dict()).json(
                indent=4, exclude_none=True
            )

        test_file = TestSH(command=feature_definition_model.test_command or "").to_str()

        install_command_file = InstallCommandSH(
            command=feature_definition_model.install_command or ""
        ).to_str()

        dependencies_file = DependenciesSH(
            feature_definition_model.dependencies, feature_definition_model.options
        ).to_str()

        install_file = InstallSH().to_str()

        dir_obj = Directory()
        dir_obj[f"test/{feature_definition_model.id}/test.sh"] = File(
            test_file.encode()
        )
        dir_obj[f"src/{feature_definition_model.id}/dependencies.sh"] = File(
            dependencies_file.encode()
        )
        dir_obj[f"src/{feature_definition_model.id}/install_command.sh"] = File(
            install_command_file.encode()
        )
        dir_obj[f"src/{feature_definition_model.id}/install.sh"] = File(
            install_file.encode()
        )

        dir_obj[f"src/{feature_definition_model.id}/devcontainer-feature.json"] = File(
            feature_json_file.encode()
        )

        dir_obj.create(output_dir.as_posix())

    else:
        raise ValueError(f"invalid output type: {output_type}")
