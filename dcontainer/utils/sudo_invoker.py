import sys
from typing import Type

import invoke

sys.stdout.reconfigure(
    encoding="utf-8"
)  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error
sys.stderr.reconfigure(
    encoding="utf-8"
)  # some processes will print in utf-8 while original stdout accept only ascii, causing a "UnicodeEncodeError: 'ascii' codec can't encode characters" error


class SudoInvoker:
    class SudoInvokerException(Exception):
        def __init__(self, command: str, response) -> None:
            self.command = command
            self.response = response

        def __str__(self):
            return f"The command '{self.command}' failed. return_code: {self.response.return_code}. see logs for details."

    @staticmethod
    def invoke(
        command: str,
        exception_class: Type[
            "SudoInvoker.SudoInvokerException"
        ] = SudoInvokerException,
    ) -> None:
        response = invoke.sudo(
            command, out_stream=sys.stdout, err_stream=sys.stderr, pty=True
        )
        if not response.ok:
            raise exception_class(command=command, response=response)
