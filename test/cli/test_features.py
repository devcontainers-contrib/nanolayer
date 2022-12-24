import os
from devcontainer_contrib.cli.features import generate, OutputType
from helpers import RESOURCE_DIR
import pathlib

ACT_FEATURE_DEFINITION = os.path.join(RESOURCE_DIR, "alp-asdf-feature-definition.json")
FEATURE_ID = "alp-asdf"
TEST_IMAGE = "mcr.microsoft.com/devcontainers/base:debian"


def test_features_generate_dependencies(tmp_path: str) -> None:
    generate(
        feature_definition=ACT_FEATURE_DEFINITION,
        output_dir=tmp_path,
        output_type=OutputType.dependencies,
    )

    assert os.path.isfile(os.path.join(tmp_path, "dependencies.sh"))


def test_feature_generate_test(tmp_path: str) -> None:
    generate(
        feature_definition=ACT_FEATURE_DEFINITION,
        output_dir=tmp_path,
        output_type=OutputType.test,
    )

    assert os.path.isfile(os.path.join(tmp_path, "test.sh"))


def test_feature_generate_feature_dir(shell, tmp_path: pathlib.Path) -> None:
    tmp_path_str = tmp_path.as_posix()
    generate(
        feature_definition=ACT_FEATURE_DEFINITION,
        output_dir=tmp_path,
        output_type=OutputType.feature_dir,
    )

    assert os.path.isfile(os.path.join(tmp_path_str, "test", FEATURE_ID, "test.sh"))
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", FEATURE_ID, "dependencies.sh")
    )
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", FEATURE_ID, "devcontainer-feature.json")
    )
    assert os.path.isfile(os.path.join(tmp_path_str, "src", FEATURE_ID, "install.sh"))
    assert os.path.isfile(
        os.path.join(tmp_path_str, "src", FEATURE_ID, "install_command.sh")
    )
    response = shell.run(
        f"devcontainer features test -p {tmp_path_str} -f {FEATURE_ID}  -i {TEST_IMAGE}",
        shell=True,
    )
    print(response.stdout)
    print(response.stderr)

    assert response.exitcode == 0
