from typing import List

import pytest
from helpers import execute_current_python_in_container


@pytest.mark.parametrize(
    "packages,ppas,test_command,image,excpected_result,docker_platform",
    [
        (
            "neovim",
            "ppa:neovim-ppa/stable",
            "nvim --version",
            "mcr.microsoft.com/devcontainers/base:ubuntu",
            0,
            "linux/amd64",
        ),
        (
            "neovim",
            "ppa:neovim-ppa/stable",
            "nvim --version",
            "mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye",
            0,
            "linux/amd64",
        ),
        (
            "neovim",
            "",
            "nvim --version",
            "mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye",
            0,
            "linux/amd64",
        ),
        (
            "neovim",
            "",
            "nvim --version",
            "mcr.microsoft.com/vscode/devcontainers/python:3.10-bullseye",
            0,
            "linux/arm64",
        ),
    ],
)
def test_aptitude_install(
    packages: str,
    ppas: str,
    test_command,
    image: str,
    excpected_result: int,
    docker_platform: str,
) -> None:
    ppas_cmd = f" --ppas {ppas} " if ppas else ""
    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m nanolayer install aptitude {packages} {ppas_cmd} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command, image=image, docker_platform=docker_platform
    )
