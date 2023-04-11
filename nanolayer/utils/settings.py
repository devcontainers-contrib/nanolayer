import os
from typing import Optional

from pydantic import BaseSettings


class NanolayerSettings(BaseSettings):
    class Config:
        env_prefix = "NANOLAYER_"

    cli_location: str = ""
    propagate_cli_location: str = "1"
    force_cli_installation: str = ""

    analytics_id: str = "https://2a5d4cc20cb94a8cbb691df3bcc69f0f@o4504983808901120.ingest.sentry.io/4504983813685248"
    enable_analytics: bool = True

    verbose: str = ""


ENV_CLI_LOCATION = f"{NanolayerSettings.Config.env_prefix}CLI_LOCATION"

ENV_ENABLE_ANALYTICS = f"{NanolayerSettings.Config.env_prefix}ENABLE_ANALYTICS"
ENV_ANALYTICS_ID = f"{NanolayerSettings.Config.env_prefix}ANALYTICS_ID"

ENV_PROPAGATE_CLI_LOCATION = (
    f"{NanolayerSettings.Config.env_prefix}PROPAGATE_CLI_LOCATION"
)
ENV_FORCE_CLI_INSTALLATION = (
    f"{NanolayerSettings.Config.env_prefix}FORCE_CLI_INSTALLATION"
)
ENV_VERBOSE = f"{NanolayerSettings.Config.env_prefix}VERBOSE"
