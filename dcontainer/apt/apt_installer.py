import platform
from typing import Dict, List, Optional

from dcontainer.utils.invoker import Invoker
from dcontainer.utils.linux_information_desk import LinuxInformationDesk


class AptInstaller:
    class PPASOnNonUbuntu(Exception):
        pass

    class AptUpdateFailed(Invoker.InvokerException):
        pass

    class AddPPAsFailed(Invoker.InvokerException):
        pass

    class RemovePPAsFailed(Invoker.InvokerException):
        pass

    class CleanUpFailed(Invoker.InvokerException):
        pass

    @staticmethod
    def normalize_ppas(ppas: List[str]) -> List[str]:
        # normalize ppas to have the ppa: initials
        for ppa_idx, ppa in enumerate(ppas):
            if "ppa:" != ppa[:4]:
                ppas[ppa_idx] = f"ppa:{ppa}"
        return ppas

    @staticmethod
    def _parse_env_file(path: str) -> Dict[str, str]:
        with open(path, "r") as f:
            return dict(
                tuple(line.replace("\n", "").split("="))
                for line in f.readlines()
                if not line.startswith("#")
            )

    @classmethod
    def is_ubuntu(cls) -> bool:
        return (
            LinuxInformationDesk.get_release_id()
            == LinuxInformationDesk.LinuxReleaseID.ubuntu
        )

    @classmethod
    def is_debian_like(cls) -> bool:
        return (
            LinuxInformationDesk.get_release_id(id_like=True)
            == LinuxInformationDesk.LinuxReleaseID.ubuntu
        )

    @classmethod
    def install(
        cls,
        packages: List[str],
        ppas: Optional[List[str]] = None,
        force_ppas_on_non_ubuntu: bool = False,
        remove_ppas_on_completion: bool = True,
        remove_cache_on_completion: bool = True,
    ) -> None:
        assert (
            cls.is_debian_like()
        ), "apt should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"
        if ppas and not cls.is_ubuntu() and not force_ppas_on_non_ubuntu:
            raise cls.PPASOnNonUbuntu()

        normalized_ppas = cls.normalize_ppas(ppas)
        software_properties_common_installed = False
        try:
            Invoker.invoke(
                command="apt update -y",
                raise_on_failure=True,
                exception_class=cls.AptUpdateFailed,
            )

            if ppas:
                if (
                    Invoker.invoke(
                        "dpkg -s software-properties-common", raise_on_failure=False
                    )
                    != 0
                ):
                    Invoker.invoke(
                        command="apt install -y software-properties-common",
                        raise_on_failure=True,
                        exception_class=cls.AddPPAsFailed,
                    )

                    software_properties_common_installed = True

                for ppa in normalized_ppas:
                    Invoker.invoke(
                        command=f"add-apt-repository -y {ppa}",
                        raise_on_failure=True,
                        exception_class=cls.AddPPAsFailed,
                    )

                Invoker.invoke(
                    command="apt update -y",
                    raise_on_failure=True,
                    exception_class=cls.AptUpdateFailed,
                )

            Invoker.invoke(
                command=f"apt install -y --no-install-recommends {' '.join(packages)}",
                raise_on_failure=True,
                exception_class=cls.AptUpdateFailed,
            )

        finally:
            if remove_ppas_on_completion:
                for ppa in normalized_ppas:
                    Invoker.invoke(
                        command=f"add-apt-repository -y --remove {ppa}",
                        raise_on_failure=True,
                        exception_class=cls.RemovePPAsFailed,
                    )
                if software_properties_common_installed:
                    Invoker.invoke(
                        command="apt -y remove software-properties-common",
                        raise_on_failure=True,
                        exception_class=cls.RemovePPAsFailed,
                    )

            if remove_cache_on_completion:
                Invoker.invoke(
                    command="rm -rf /var/lib/apt/lists/*",
                    raise_on_failure=True,
                    exception_class=cls.CleanUpFailed,
                )