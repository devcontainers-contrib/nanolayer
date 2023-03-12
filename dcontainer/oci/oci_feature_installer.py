import logging
import os
import pwd
import tempfile
from typing import Dict, Optional, Union
import sys
import os
import invoke

from dcontainer.models.devcontainer_feature import Feature
from dcontainer.oci.oci_feature import OCIFeature
from dcontainer.settings import DContainerSettings, ENV_CLI_LOCATION, ENV_PROPAGATE_CLI_LOCATION,  ENV_FORCE_CLI_INSTALLATION, ENV_VERBOSE

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

    @classmethod
    def install(
        cls,
        feature_oci: OCIFeature,
        options: Optional[Dict[str, Union[str, bool]]] = None,
        remote_user_name: Optional[str] = None,
        verbose: bool = False,
    ) -> None:
        if options is None:
            options = {}
        options = cls._resolve_options(
            feature_obj=feature_oci.get_devcontainer_feature_obj(), options=options
        )
        logger.info("resolved options: %s", str(options))

        remote_user = cls._resolve_remote_user(remote_user_name)
        logger.info("resolved remote user: %s", remote_user)

        env_variables = {}
        env_variables[cls._REMOTE_USER_ENV] = remote_user.pw_name
        env_variables[cls._REMOTE_USER_HOME_ENV] = remote_user.pw_dir
        for option_name, option_value in options.items():
            if isinstance(option_value, bool):
                option_value = "true" if option_value else "false"
            env_variables[option_name.upper()] = option_value

        try:
            settings = DContainerSettings()

            if settings.verbose == "1":
                verbose = True 

            env_variables[ENV_VERBOSE] = settings.verbose
            env_variables[ENV_FORCE_CLI_INSTALLATION] = settings.force_cli_installation
            env_variables[ENV_PROPAGATE_CLI_LOCATION] = settings.propagate_cli_location

            if settings.propagate_cli_location == "1":
                if settings.cli_location != "":
                    env_variables[ENV_CLI_LOCATION] = settings.cli_location
                elif getattr(sys, 'frozen', False):
                    env_variables[ENV_CLI_LOCATION] = sys.executable
            else:
                # override it with empty string in case it already exists 
                env_variables[ENV_CLI_LOCATION] = ""
            
        except Exception as e:
            logger.warning(f"could not create settings: {str(e)}")
            

        cls._install_feature(feature_oci=feature_oci, envs=env_variables, verbose=verbose)

    @classmethod
    def _escape_quotes(cls, value: str) -> str:
        return value.replace('"', '\\"')
    
    @classmethod
    def _install_feature(cls, 
                         feature_oci: OCIFeature, 
                         envs: Dict[str, str], 
                         verbose: bool = False) -> None:
        env_variables_cmd = " ".join(
            [f'{env_name}="{cls._escape_quotes(env_value)}"' for env_name, env_value in envs.items()]
        )
    
    
        with tempfile.TemporaryDirectory() as tempdir:
            feature_oci.download_and_extract(tempdir)

            sys.stdout.reconfigure(encoding='utf-8')  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error
            sys.stderr.reconfigure(encoding='utf-8')  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error
            
            response = invoke.run(
                f"cd {tempdir} && \
                chmod +x -R . && \
                sudo {env_variables_cmd} bash -i {'-x' if verbose else ''} ./{cls._FEATURE_ENTRYPOINT}",
                out_stream=sys.stdout,
                err_stream=sys.stderr,
            )

            if not response.ok:
                raise OCIFeatureInstaller.FeatureInstallationException(
                    f"feature {feature_oci.path} failed to install. return_code: {response.return_code}. see logs for error reason."
                )

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
