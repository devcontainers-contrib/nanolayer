import os
from devcontainer_contrib.cli.features import generate, OutputType
from helpers import RESOURCE_DIR
import pathlib
import pytest

FEATURE_DEFENITIONS = {
    "alp-asdf": os.path.join(
        RESOURCE_DIR, "test_feature_definitions", "alp-asdf", "feature-definition.json"
    ),
    "angular-cli": os.path.join(
        RESOURCE_DIR,
        "test_feature_definitions",
        "angular-cli",
        "feature-definition.json",
    ),
    "ansible": os.path.join(
        RESOURCE_DIR, "test_feature_definitions", "ansible", "feature-definition.json"
    ),
    "localstack": os.path.join(
        RESOURCE_DIR,
        "test_feature_definitions",
        "localstack",
        "feature-definition.json",
    ),
}

TEST_IMAGE = "mcr.microsoft.com/devcontainers/base:debian"


@pytest.mark.parametrize(
    "feature_id,feature_definition", [(k, v) for k, v in FEATURE_DEFENITIONS.items()]
)
def test_features_generate_dependencies(
    tmp_path: str, feature_id: str, feature_definition: str
) -> None:
    generate(
        feature_definition=feature_definition,
        output_dir=tmp_path,
        output_type=OutputType.dependencies,
    )

    assert os.path.isfile(os.path.join(tmp_path, "dependencies.sh"))


@pytest.mark.parametrize(
    "feature_id,feature_definition", [(k, v) for k, v in FEATURE_DEFENITIONS.items()]
)
def test_feature_generate_test(
    tmp_path: str, feature_id: str, feature_definition: str
) -> None:
    generate(
        feature_definition=feature_definition,
        output_dir=tmp_path,
        output_type=OutputType.test,
    )

    assert os.path.isfile(os.path.join(tmp_path, "test.sh"))


@pytest.mark.parametrize(
    "feature_id,feature_definition", [(k, v) for k, v in FEATURE_DEFENITIONS.items()]
)
def test_feature_generate_feature_dir(
    shell, tmp_path: pathlib.Path, feature_id: str, feature_definition: str
) -> None:
    tmp_path_str = tmp_path.as_posix()
    generate(
        feature_definition=feature_definition,
        output_dir=tmp_path,
        output_type=OutputType.feature_dir,
    )

    assert os.path.isfile(os.path.join(tmp_path_str, "test", feature_id, "test.sh"))
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", feature_id, "dependencies.sh")
    )
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", feature_id, "devcontainer-feature.json")
    )
    assert os.path.isfile(os.path.join(tmp_path_str, "src", feature_id, "install.sh"))
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", feature_id, "install_command.sh")
    )
    response = shell.run(
        f"devcontainer features test -p {tmp_path_str} -f {feature_id}  -i {TEST_IMAGE}",
        shell=True,
    )
    print(response.stdout)
    print(response.stderr)

    assert response.exitcode == 0
