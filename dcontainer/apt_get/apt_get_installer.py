from typing import List, Optional, Type
import platform
import invoke
import sys


class InteractiveSudoInvoker:
    class InteractiveSudoInvokerException(Exception):
        def __init__(self, command: str, response) -> None:
            self.command = command
            self.response = response

        def __str__(self):
            return f"The command '{self.command}' failed. return_code: {self.response.return_code}. see logs for details."

    @staticmethod
    def invoke(
        command: str,
        exception_class: Type["InteractiveSudoInvoker.InteractiveSudoInvokerException"],
    ) -> None:
        response = invoke.sudo(
            command, out_stream=sys.stdout, err_stream=sys.stderr, pty=True
        )
        if not response.ok:
            raise exception_class(command=command, response=response)



class AptGetInstaller:
    class PPASOnNonUbuntu(Exception):
        pass

    class AptGetUpdateFailed(InteractiveSudoInvoker.InteractiveSudoInvokerException):
        pass

    class AddPPAsFailed(InteractiveSudoInvoker.InteractiveSudoInvokerException):
        pass

    class RemovePPAsFailed(InteractiveSudoInvoker.InteractiveSudoInvokerException):
        pass

    class CleanUpFailed(InteractiveSudoInvoker.InteractiveSudoInvokerException):
        pass

    @staticmethod
    def normalize_ppas(ppas: List[str]) -> List[str]:
        # normalize ppas to have the ppa: initials
        for ppa_idx, ppa in enumerate(ppas):
            if "ppa:" != ppa[:4]:
                ppas[ppa_idx] = f"ppa:{ppa}"
        return ppas

    @staticmethod
    def install(
        packages: List[str],
        ppas: Optional[List[str]] = None,
        force_ppas_on_non_ubuntu: bool = True,
        remove_ppas_on_completion: bool = True,
        remove_cache_on_completion: bool = True,
    ) -> None:
        if (
            ppas
            and not "ubuntu" in platform.version().lower()
            and not force_ppas_on_non_ubuntu
        ):
            raise AptGetInstaller.PPASOnNonUbuntu()

        normalized_ppas = AptGetInstaller.normalize_ppas(ppas)

        try:
            InteractiveSudoInvoker.invoke(
                command="apt-get update -y",
                exception_class=AptGetInstaller.AptGetUpdateFailed,
            )

            if ppas:
                InteractiveSudoInvoker.invoke(
                    command="apt-get install software-properties-common",
                    exception_class=AptGetInstaller.AddPPAsFailed,
                )

                for ppa in normalized_ppas:
                    InteractiveSudoInvoker.invoke(
                        command=f"add-apt-repository -y {ppa}",
                        exception_class=AptGetInstaller.AddPPAsFailed,
                    )

                InteractiveSudoInvoker.invoke(
                    command="apt-get update -y",
                    exception_class=AptGetInstaller.AptGetUpdateFailed,
                )

            InteractiveSudoInvoker.invoke(
                command=f"apt-get -y install --no-install-recommends {' '.join(packages)}",
                exception_class=AptGetInstaller.AptGetUpdateFailed,
            )

        finally:
            if remove_ppas_on_completion:
                for ppa in normalized_ppas:
                    InteractiveSudoInvoker.invoke(
                        command=f"add-apt-repository -y --remove {ppa}",
                        exception_class=AptGetInstaller.RemovePPAsFailed,
                    )

            if remove_cache_on_completion:
                InteractiveSudoInvoker.invoke(
                    command="rm -rf /var/lib/apt/lists/*",
                    exception_class=AptGetInstaller.CleanUpFailed,
                )
