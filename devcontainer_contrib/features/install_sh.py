HEADER = """#!/usr/bin/env bash

set -e

source ./dependencies.sh

source ./install_command.sh

"""


class InstallSH:
    def to_str(self) -> str:
        return HEADER
