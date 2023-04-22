import logging
import os
import pwd
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union

from nanolayer.installers.devcontainer_feature.models.devcontainer_feature import (
    Feature,
)
from nanolayer.installers.devcontainer_feature.oci_feature import OCIFeature
from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk
from nanolayer.utils.settings import (
    ENV_CLI_LOCATION,
    ENV_FORCE_CLI_INSTALLATION,
    ENV_PROPAGATE_CLI_LOCATION,
    ENV_VERBOSE,
    NanolayerSettings,
)

logger = logging.getLogger(__name__)


class OCIFeatureInstaller:
    class FeatureInstallationException(Exception):
        pass

    class NoPremissions(PermissionError):
        pass

    _ORDERED_BASE_REMOTE_USERS = ("vscode", "node", "codespace")
    _FALLBACK_USER_ID_A = (
        1000  # user 1000 (mostly the base user of the contianer eg. "ubuntu" etc)
    )
    _FALLBACK_USER_ID_B = 0  # user 0 (root)

    _REMOTE_USER_ENV = "_REMOTE_USER"
    _REMOTE_USER_HOME_ENV = "_REMOTE_USER_HOME"

    _FEATURE_ENTRYPOINT = "install.sh"

    _PROFILE_DIR = "/etc/profile.d"

    @classmethod
    def install(
        cls,
        feature_ref: str,
        options: Optional[Dict[str, Union[str, bool]]] = None,
        envs: Optional[Dict[str, str]] = None,
        remote_user: Optional[str] = None,
        verbose: bool = False,
    ) -> None:
        if not LinuxInformationDesk.has_root_privileges():
            raise cls.NoPremissions(
                "Installer must be run as root. Use sudo, su, or add 'USER root' to your Dockerfile before running this command."
            )

        if options is None:
            options = {}

        if envs is None:
            envs = {}

        feature_obj = OCIFeature.get_devcontainer_feature_obj(
            oci_feature_ref=feature_ref
        )

        options = cls._resolve_options(feature_obj=feature_obj, options=options)
        logger.info("resolved options: %s", str(options))

        remote_user = cls._resolve_remote_user(remote_user)
        logger.info("resolved remote user: %s", remote_user)

        envs[cls._REMOTE_USER_ENV] = remote_user.pw_name
        envs[cls._REMOTE_USER_HOME_ENV] = remote_user.pw_dir
        for option_name, option_value in options.items():
            if isinstance(option_value, bool):
                option_value = "true" if option_value else "false"
            envs[option_name.upper()] = option_value

        try:
            settings = NanolayerSettings()

            if settings.verbose == "1":
                verbose = True

            envs[ENV_VERBOSE] = settings.verbose
            envs[ENV_FORCE_CLI_INSTALLATION] = settings.force_cli_installation
            envs[ENV_PROPAGATE_CLI_LOCATION] = settings.propagate_cli_location

            if settings.propagate_cli_location == "1":
                if settings.cli_location != "":
                    envs[ENV_CLI_LOCATION] = settings.cli_location
                elif getattr(sys, "frozen", False):
                    envs[ENV_CLI_LOCATION] = sys.executable
            else:
                # override it with empty string in case it already exists
                envs[ENV_CLI_LOCATION] = ""

        except Exception as e:
            logger.warning(f"could not create settings: {str(e)}")

        env_variables_cmd = " ".join(
            [
                f'{env_name}="{cls._escape_quotes(env_value)}"'
                for env_name, env_value in envs.items()
            ]
        )

        with tempfile.TemporaryDirectory() as tempdir:
            OCIFeature.download_and_extract(
                oci_feature_ref=feature_ref, output_dir=tempdir
            )

            command = f"cd {tempdir} && chmod +x -R . && {env_variables_cmd} bash "

            # will make sure it will get the env variable that are
            # defined in various rc files
            command += " -i "

            # most scripts assume non interactive (plain #!/bin/bash shebang),
            # disabling history expansion will make scripts behave closer to non-interactive way
            command += " +H "

            command += " -x " if verbose else ""

            command += f"./{cls._FEATURE_ENTRYPOINT}"

            Invoker.invoke(command)

            cls._set_permanent_envs(feature_obj)

    @classmethod
    def _set_permanent_envs(cls, feature: Feature) -> None:
        if feature.containerEnv is None:
            return

        feature_profile_dir = Path(cls._PROFILE_DIR)
        feature_profile_dir.mkdir(exist_ok=True, parents=True)
        feature_profile_file = feature_profile_dir.joinpath(
            f"nanolayer-{feature.id}.sh"
        )

        if not feature_profile_file.exists():
            feature_profile_file.touch()

        with open(feature_profile_file, "r") as f:
            current_content = f.read()

        modified = False
        for env_name, env_value in feature.containerEnv.items():
            statement = f"export {env_name}={env_value}"
            if statement not in current_content:
                current_content += f"\n{statement}"

                modified = True

        if modified:
            with open(feature_profile_file, "w") as f:
                f.write(current_content)

    @classmethod
    def _escape_quotes(cls, value: str) -> str:
        return value.replace('"', '\\"')

    @classmethod
    def _resolve_options(
        cls, feature_obj: Feature, options: Dict[str, Union[str, bool]]
    ) -> Dict[str, Union[str, bool]]:
        options_definitions = feature_obj.options or {}

        for option_name, option_obj in options_definitions.items():
            if (option_name not in options) or (options[option_name] == ""):
                options[option_name] = option_obj.__root__.default
        return options

    @classmethod
    def _resolve_remote_user(
        cls, remote_user_name: Optional[str] = None
    ) -> pwd.struct_passwd:
        if remote_user_name is not None:
            try:
                main_user = pwd.getpwnam(remote_user_name)
                return main_user
            except KeyError:
                logger.warning(
                    "The user name '%s' was not found, attempting fallback",
                    remote_user_name,
                )

        for user_name in cls._ORDERED_BASE_REMOTE_USERS:
            try:
                main_user = pwd.getpwnam(user_name)
                return main_user
            except KeyError:
                pass

        try:
            main_user = pwd.getpwuid(cls._FALLBACK_USER_ID_A)
            return main_user
        except KeyError:
            pass

        try:
            main_user = pwd.getpwuid(cls._FALLBACK_USER_ID_B)
            return main_user
        except KeyError:
            pass

        return pwd.getpwuid(os.getuid())
