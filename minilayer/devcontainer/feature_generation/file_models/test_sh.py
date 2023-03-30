from typing import List

from easyfs import File

HEADER = """#!/bin/bash -i

set -e

source dev-container-features-test-lib

{test_commands}

reportResults
"""


class TestSH(File):
    def __init__(self, commands: List[str]) -> None:
        super().__init__(
            HEADER.format(
                test_commands="\n\n".join(
                    [f'check "{command}" {command}' for command in commands]
                )
            ).encode()
        )
