import os
from typing import Optional

from pydantic import BaseSettings

class DContainerSettings(BaseSettings):
    class Config:
        env_prefix = "DCONTAINER_"

    cli_location: Optional[str] = ""
    propagate_cli_location: Optional[bool] = True
    reuse_cli_location: Optional[bool] = True
    verbose: Optional[bool] = None

ENV_CLI_LOCATION = f"{DContainerSettings.Config.env_prefix}CLI_LOCATION"
ENV_PROPAGATE_CLI_LOCATION = f"{DContainerSettings.Config.env_prefix}PROPAGATE_CLI_LOCATION"
ENV_REUSE_CLI_LOCATION = f"{DContainerSettings.Config.env_prefix}REUSE_CLI_LOCATION"
