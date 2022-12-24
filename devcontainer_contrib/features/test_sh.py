HEADER = """#!/usr/bin/env bash

set -e

source dev-container-features-test-lib

check "{command}" {command}

reportResults
"""


class TestSH:
    def __init__(self, command: str) -> None:
        self.command = command

    def to_str(self) -> str:
        return HEADER.format(command=self.command)
