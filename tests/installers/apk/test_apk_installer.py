import pytest
from helpers import execute_current_python_in_container


@pytest.mark.parametrize(
    "packages,test_command,image,excpected_result,docker_platform",
    [
        (
            "bash",
            "which bash",
            "alpine",
            0,
            "linux/amd64",
        )
    ],
)
def test_apk_install(
    packages: str,
    test_command,
    image: str,
    excpected_result: int,
    docker_platform: str,
) -> None:
    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m nanolayer install apk {packages} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
        docker_platform=docker_platform,
    )
