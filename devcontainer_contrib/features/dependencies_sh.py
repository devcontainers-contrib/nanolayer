from typing import Optional, Dict
from devcontainer_contrib.features.feature_sh import FeatureSH
from devcontainer_contrib.models.devcontainer_feature_definition import (
    FeatureDependencies,
    FeatureOption,
)


HEADER = """#!/usr/bin/env bash
set -e

ensure_curl () {{
    if ! type curl >/dev/null 2>&1; then
        apt-get update -y && apt-get -y install --no-install-recommends curl
    fi 
}}

ensure_curl

{dependency_installation_lines}
"""


class DependenciesSH:
    REF_PREFIX = "$options."

    def __init__(
        self,
        dependencies: Optional[FeatureDependencies],
        options: Optional[Dict[str, FeatureOption]],
    ) -> None:
        self.dependencies = dependencies
        self.options = options

    @staticmethod
    def is_param_ref(param_value: str) -> bool:
        return param_value.startswith(DependenciesSH.REF_PREFIX)

    @staticmethod
    def resolve_param_ref(
        param_ref: str, options: Optional[Dict[str, FeatureOption]]
    ) -> str:
        if options is None:
            raise ValueError(
                f"option reference was given: '{param_ref}' but no options exists"
            )

        option_name = param_ref.replace(DependenciesSH.REF_PREFIX, "")

        option = options.get(option_name, None)
        if option is None:
            raise ValueError(
                f"could not resolve option reference: '{param_ref}' please ensure you spelled the option name right ({option})"
            )
        return f"${option_name}".upper()

    def to_str(self) -> str:
        if self.dependencies is None or len(self.dependencies) == 0:
            return ""

        installation_lines = []
        for feature_oci, params in self.dependencies.items():
            resolved_params = {}
            for param_name, param_value in params.items():
                if isinstance(param_value, str):
                    if DependenciesSH.is_param_ref(param_value):
                        param_value = DependenciesSH.resolve_param_ref(
                            param_value, self.options
                        )

                resolved_params[param_name] = param_value
            installation_lines.append(
                FeatureSH(feature_oci).create_install_command(resolved_params)
            )

        return HEADER.format(
            dependency_installation_lines="\n".join(installation_lines)
        )
