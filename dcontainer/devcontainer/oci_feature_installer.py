import logging
import os
import pwd
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union

import invoke

from dcontainer.devcontainer.models.devcontainer_feature import Feature
from dcontainer.devcontainer.oci_feature import OCIFeature
from dcontainer.settings import (
    ENV_CLI_LOCATION,
    ENV_FORCE_CLI_INSTALLATION,
    ENV_PROPAGATE_CLI_LOCATION,
    ENV_VERBOSE,
    DContainerSettings,
)

logger = logging.getLogger(__name__)


class OCIFeatureInstaller:
    class FeatureInstallationException(Exception):
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
            settings = DContainerSettings()

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

            sys.stdout.reconfigure(
                encoding="utf-8"
            )  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error
            sys.stderr.reconfigure(
                encoding="utf-8"
            )  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error

            response = invoke.run(
                f"cd {tempdir} && \
                chmod +x -R . && \
                sudo {env_variables_cmd} bash -i {'-x' if verbose else ''} ./{cls._FEATURE_ENTRYPOINT}",
                out_stream=sys.stdout,
                err_stream=sys.stderr,
                pty=True,
            )

            if not response.ok:
                raise OCIFeatureInstaller.FeatureInstallationException(
                    f"feature {feature_ref} failed to install. return_code: {response.return_code}. see logs for error reason."
                )

            cls._set_permanent_envs(feature_obj)

    @classmethod
    def _set_permanent_envs(cls, feature: Feature) -> None:
        if feature.containerEnv is None:
            return

        feature_profile_dir = Path(cls._PROFILE_DIR)
        feature_profile_dir.mkdir(exist_ok=True, parents=True)
        feature_profile_file = feature_profile_dir.joinpath(
            f"dcontainer-{feature.id}.sh"
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
