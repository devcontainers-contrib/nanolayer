from typing import Dict, Union

FEATURE_INSTALLER_LINK = "https://raw.githubusercontent.com/devcontainers-contrib/cli/main/resources/install-feature.sh"


class FeatureSH:
    def __init__(self, feature_oci: str) -> None:
        self.feature_oci = feature_oci

    def create_install_command(self, params: Dict[str, Union[str, bool]]):
        envs = {}
        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                envs[param_name.upper()] = param_value
            else:
                envs[param_name.upper()] = str(param_value).lower()

        stringified_envs = " ".join([f"{env}={val}" for env, val in envs.items()])

        return f"{stringified_envs} source <(curl -s {FEATURE_INSTALLER_LINK}) {self.feature_oci}"
