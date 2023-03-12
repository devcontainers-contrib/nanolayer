import os
from typing import Optional

from pydantic import BaseSettings


class DContainerSettings(BaseSettings):
    class Config:
        env_prefix = "DCONTAINER_"
