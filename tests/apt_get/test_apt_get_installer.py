from typing import List

import pytest
from helpers import execute_current_python_in_container


@pytest.mark.parametrize(
    "packages,ppas,test_command,image,excpected_result",
    [
        (
            ["neovim"],
            ["ppa:neovim-ppa/stable"],
            "nvim --version",
            "mcr.microsoft.com/devcontainers/base:ubuntu",
            0,
        ),
        (
            ["neovim"],
            ["ppa:neovim-ppa/stable"],
            "nvim --version",
            "mcr.microsoft.com/devcontainers/base:debian",
            1,
        ),
        (
            ["neovim"],
            [],
            "nvim --version",
            "mcr.microsoft.com/devcontainers/base:debian",
            0,
        ),
    ],
)
def test_apt_get_install(
    packages: List[str],
    ppas: List[str],
    test_command,
    image: str,
    excpected_result: int,
) -> None:
    packages_cmd = " ".join([f"{package} " for package in packages])
    ppas_cmd = " ".join([f"--ppa {ppa}" for ppa in ppas])
    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m dcontainer install apt-get {packages_cmd} {ppas_cmd} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
    )
