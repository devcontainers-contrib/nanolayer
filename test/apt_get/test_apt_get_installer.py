
from typing import List

import pytest
from helpers import execute_current_python_in_container


@pytest.mark.parametrize(
    "packages,ppas,test_command,image",
    [
        (
            ["neovim"],
            ["ppa:neovim-ppa/stable"],
            "nvim --version",
            "mcr.microsoft.com/devcontainers/base:ubuntu",
        )
    ],
)
def test_apt_get_install(
    packages: List[str], ppas: List[str], test_command, image: str
) -> None:
    packages_cmd = " ".join([f"{package} " for package in packages])
    ppas_cmd = " ".join([f"--ppa {ppa}" for ppa in ppas])
    full_test_command = f"python3 -m dcontainer install apt-get {packages_cmd} {ppas_cmd} && {test_command}"

    assert execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
    )
