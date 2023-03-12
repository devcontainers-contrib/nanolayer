import os
from typing import Optional

from pydantic import BaseSettings


class DContainerSettings(BaseSettings):
    class Config:
        env_prefix = "DCONTAINER_"

    cli_location: str = ""
    propagate_cli_location: str = "1"
    force_cli_installation: str = ""
    verbose: str = ""


ENV_CLI_LOCATION = f"{DContainerSettings.Config.env_prefix}CLI_LOCATION"
ENV_PROPAGATE_CLI_LOCATION = (
    f"{DContainerSettings.Config.env_prefix}PROPAGATE_CLI_LOCATION"
)
ENV_FORCE_CLI_INSTALLATION = (
    f"{DContainerSettings.Config.env_prefix}FORCE_CLI_INSTALLATION"
)
ENV_VERBOSE = f"{DContainerSettings.Config.env_prefix}VERBOSE"
