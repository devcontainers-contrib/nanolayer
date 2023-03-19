
from typing import List, Optional

import pytest
from helpers import execute_current_python_in_container

@pytest.mark.skip(reason="no way of currently testing this")
@pytest.mark.parametrize(
    "test_command,excpected_result,image,repo,target,asset_regex",
    [
        (
            "doctl version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "digitalocean/doctl",
            "doctl"
        ),
        (
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "argoproj/argo-cd",
            "argocd"
        ),
        (
            "which kubectx",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubectx"
        ),
        (
            "which kubens",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubens"
        ),
        (
            "terrascan version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "tenable/terrascan",
            "terrascan"
        ),
        (
            "gh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "cli/cli",
            "gh"
        ),
        (
            "pwsh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "PowerShell/PowerShell",
            "pwsh"
        )
    ],
)
def test_gh_release_install(
    test_command, excpected_result: int,  image: str, repo: List[str], target: str, 
) -> None:

    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m dcontainer install gh-release {repo} {target} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
    )

@pytest.mark.parametrize(
    "test_command,excpected_result,image,repo,target,asset_regex",
    [
        (
            "pwsh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "PowerShell/PowerShell",
            "pwsh",
            "powershell-7.3.3-linux-x64.tar.gz"
        ),
    ],
)
def test_gh_release_install_with_regex(
    test_command, excpected_result: int,  image: str, repo: List[str], target: str, asset_regex: Optional[str]=None,
) -> None:

    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m dcontainer install gh-release {repo} {target} --asset-regex {asset_regex} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
    )

