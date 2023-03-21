from typing import List, Optional

import pytest
from helpers import execute_current_python_in_container


# @pytest.mark.skip(reason="not implemented yet")
@pytest.mark.parametrize(
    "test_command,excpected_result,image,repo,target",
    [
        (
            "doctl version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "digitalocean/doctl",
            "doctl",
        ),
        (
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "argoproj/argo-cd",
            "argocd",
        ),
        (
            "which kubectx",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubectx",
        ),
        (
            "which kubens",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubens",
        ),
        (
            "terrascan version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "tenable/terrascan",
            "terrascan",
        ),
        (
            "gh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "cli/cli",
            "gh",
        ),
        (
            "pwsh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "PowerShell/PowerShell",
            "pwsh",
        ),
    ],
)
def test_gh_release_install(
    test_command,
    excpected_result: int,
    image: str,
    repo: List[str],
    target: str,
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
            "doctl version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "digitalocean/doctl",
            "doctl",
            "doctl-1.93.1-linux-amd64.tar.gz",
        ),
        (
            "argocd --help",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "argoproj/argo-cd",
            "argocd",
            "argocd-linux-amd64",
        ),
        (
            "which kubectx",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubectx",
            "kubectx_v0.9.4_linux_x86_64.tar.gz",
        ),
        (
            "which kubens",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "ahmetb/kubectx",
            "kubens",
            "kubens_v0.9.4_linux_x86_64.tar.gz",
        ),
        (
            "terrascan version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "tenable/terrascan",
            "terrascan",
            "terrascan_1.18.0_Linux_x86_64.tar.gz",
        ),
        (
            "gh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "cli/cli",
            "gh",
            "gh_2.24.3_linux_amd64.tar.gz",
        ),
        (
            "pwsh --version",
            0,
            "mcr.microsoft.com/devcontainers/base:debian",
            "PowerShell/PowerShell",
            "pwsh",
            "powershell-7.3.3-linux-x64.tar.gz",
        ),
    ],
)
def test_gh_release_install_with_regex(
    test_command,
    excpected_result: int,
    image: str,
    repo: List[str],
    target: str,
    asset_regex: str,
) -> None:
    full_test_command = f"sudo PYTHONPATH=$PYTHONPATH python3 -m dcontainer install gh-release {repo} {target} --asset-regex {asset_regex} && {test_command}"

    assert excpected_result == execute_current_python_in_container(
        test_command=full_test_command,
        image=image,
    )
