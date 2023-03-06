from pydantic import BaseSettings
from typing import Optional
import os


class DContainerSettings(BaseSettings):

    class Config:
        env_prefix = 'DCONTAINER_'