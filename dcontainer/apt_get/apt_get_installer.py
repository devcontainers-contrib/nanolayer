import platform
from typing import List, Optional

from dcontainer.utils.sudo_invoker import SudoInvoker


class AptGetInstaller:
    class PPASOnNonUbuntu(Exception):
        pass

    class AptGetUpdateFailed(SudoInvoker.SudoInvokerException):
        pass

    class AddPPAsFailed(SudoInvoker.SudoInvokerException):
        pass

    class RemovePPAsFailed(SudoInvoker.SudoInvokerException):
        pass

    class CleanUpFailed(SudoInvoker.SudoInvokerException):
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
            SudoInvoker.invoke(
                command="apt-get update -y",
                exception_class=AptGetInstaller.AptGetUpdateFailed,
            )

            if ppas:
                SudoInvoker.invoke(
                    command="apt-get install -y software-properties-common",
                    exception_class=AptGetInstaller.AddPPAsFailed,
                )

                for ppa in normalized_ppas:
                    SudoInvoker.invoke(
                        command=f"add-apt-repository -y {ppa}",
                        exception_class=AptGetInstaller.AddPPAsFailed,
                    )

                SudoInvoker.invoke(
                    command="apt-get update -y",
                    exception_class=AptGetInstaller.AptGetUpdateFailed,
                )

            SudoInvoker.invoke(
                command=f"apt-get install -y --no-install-recommends {' '.join(packages)}",
                exception_class=AptGetInstaller.AptGetUpdateFailed,
            )

        finally:
            if remove_ppas_on_completion:
                for ppa in normalized_ppas:
                    SudoInvoker.invoke(
                        command=f"add-apt-repository -y --remove {ppa}",
                        exception_class=AptGetInstaller.RemovePPAsFailed,
                    )

            if remove_cache_on_completion:
                SudoInvoker.invoke(
                    command="rm -rf /var/lib/apt/lists/*",
                    exception_class=AptGetInstaller.CleanUpFailed,
                )
