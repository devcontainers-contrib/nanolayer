HEADER = """#!/usr/bin/env bash

set -e

{command}
"""


class InstallCommandSH:
    def __init__(self, command: str) -> None:
        self.command = command

    def to_str(self) -> str:
        return HEADER.format(command=self.command)
