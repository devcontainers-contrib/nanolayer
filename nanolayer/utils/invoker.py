import os
import sys
from typing import Dict, Optional, Type

import invoke

sys.stdout.reconfigure(
    encoding="utf-8"
)  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error
sys.stderr.reconfigure(
    encoding="utf-8"
)  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error


class Invoker:
    class InvokerException(Exception):
        def __init__(self, command: str, error: str) -> None:
            self.command = command
            self.error = error

        def __str__(self):
            return f"The command '{self.command}' failed. error: {self.error}. see logs for details."

    @staticmethod
    def check_root_privileges() -> None:
        # credit: https://stackoverflow.com/a/69134255/5922329
        if not os.environ.get("SUDO_UID") and os.geteuid() != 0:
            raise PermissionError("You need to run this script with sudo or as root.")

    @staticmethod
    def invoke(
        command: str,
        raise_on_failure: bool = True,
        exception_class: Type["Invoker.InvokerException"] = InvokerException,
        clean_history: bool = True,
        envs: Optional[Dict[str, str]] = None,
    ) -> int:
        Invoker.check_root_privileges()

        if envs is None:
            envs = {}
        if clean_history:
            envs["HISTFILE"] = "/dev/null"

        response = invoke.run(
            command,
            out_stream=sys.stdout,
            err_stream=sys.stderr,
            pty=True,
            warn=True,
            echo=True,
            env=envs,
        )

        if raise_on_failure and not response.ok:
            raise exception_class(
                command=command, error=f"Return Code: {response.return_code}"
            )

        return response.return_code
