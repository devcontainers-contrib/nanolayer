import logging
from typing import Dict, List, Optional

import typer

from dcontainer.apt.apt_installer import AptInstaller
from dcontainer.apt_get.apt_get_installer import AptGetInstaller
from dcontainer.aptitude.aptitude_installer import AptitudeInstaller
from dcontainer.devcontainer.oci_feature_installer import OCIFeatureInstaller
from dcontainer.gh_release.gh_release_installer import GHReleaseInstaller

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_short=False)

app.command()


def _validate_args(value: Optional[List[str]]):
    if value is not None:
        for arg in value:
            splitted_arg = arg.split("=")
            if len(splitted_arg) < 2 or len(splitted_arg[0]) == 0:
                raise typer.BadParameter("Must be formatted as 'key=value'")
    return value


@app.command("devcontainer-feature")
def install_devcontainer_feature(
    feature: str,
    option: Optional[List[str]] = typer.Option(None, callback=_validate_args),
    remote_user: Optional[str] = typer.Option(None, callback=_validate_args),
    env: Optional[List[str]] = typer.Option(None, callback=_validate_args),
    verbose: bool = False,
) -> None:
    def _key_val_arg_to_dict(args: Optional[List[str]]) -> Dict[str, str]:
        if args is None:
            return {}

        args_dict = {}
        for single_arg in args:
            single_arg = _strip_if_wrapped_around(single_arg, '"')
            arg_name = single_arg.split("=")[0]
            arg_value = single_arg[len(arg_name) + 1 :]
            arg_value = _strip_if_wrapped_around(arg_value, '"')
            args_dict[arg_name] = arg_value
        return args_dict

    def _strip_if_wrapped_around(value: str, char: str) -> str:
        if len(char) > 1:
            raise ValueError(
                "For clarity sake, will only strip one character at a time"
            )

        if len(value) >= 2 and value[0] == char and value[-1] == char:
            return value.strip(char)
        return value

    options_dict = _key_val_arg_to_dict(option)
    envs_dict = _key_val_arg_to_dict(env)

    OCIFeatureInstaller.install(
        feature_ref=feature,
        envs=envs_dict,
        options=options_dict,
        remote_user=remote_user,
        verbose=verbose,
    )


@app.command("apt-get")
def install_apt_get_packages(
    package: List[str],
    ppa: Optional[List[str]] = typer.Option(None),
    force_ppas_on_non_ubuntu: bool = False,
    remove_ppas_on_completion: bool = True,
    remove_cache_on_completion: bool = True,
) -> None:
    AptGetInstaller.install(
        packages=package,
        ppas=ppa,
        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
        remove_ppas_on_completion=remove_ppas_on_completion,
        remove_cache_on_completion=remove_cache_on_completion,
    )


@app.command("apt")
def install_apt_packages(
    package: List[str],
    ppa: Optional[List[str]] = typer.Option(None),
    force_ppas_on_non_ubuntu: bool = False,
    remove_ppas_on_completion: bool = True,
    remove_cache_on_completion: bool = True,
) -> None:
    AptInstaller.install(
        packages=package,
        ppas=ppa,
        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
        remove_ppas_on_completion=remove_ppas_on_completion,
        remove_cache_on_completion=remove_cache_on_completion,
    )


@app.command("aptitude")
def install_aptitude_packages(
    package: List[str],
    ppa: Optional[List[str]] = typer.Option(None),
    force_ppas_on_non_ubuntu: bool = False,
    remove_ppas_on_completion: bool = True,
    remove_cache_on_completion: bool = True,
) -> None:
    AptitudeInstaller.install(
        packages=package,
        ppas=ppa,
        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
        remove_ppas_on_completion=remove_ppas_on_completion,
        remove_cache_on_completion=remove_cache_on_completion,
    )


@app.command("gh-release")
def install_gh_release_binary(
    repo: str,
    target: str,
    version: str = "latest",
    asset_regex: Optional[str] = None,
    force: bool = False,
    arch: Optional[str] = None,
    checksum_regex: Optional[str] = None,
    checksum: Optional[bool] = True,
) -> None:
    GHReleaseInstaller.install(
        repo=repo,
        target_name=target,
        arch=arch,
        version=version,
        asset_regex=asset_regex,
        force=force,
    )
