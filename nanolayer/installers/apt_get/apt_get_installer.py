import tempfile
from typing import List, Optional

from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class AptGetInstaller:
    class AptGetInstallerError(Exception):
        pass

    @staticmethod
    def normalize_ppas(ppas: List[str]) -> List[str]:
        # normalize ppas to have the ppa: initials
        for ppa_idx, ppa in enumerate(ppas):
            if "ppa:" != ppa[:4]:
                ppas[ppa_idx] = f"ppa:{ppa}"
        return ppas

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
            == LinuxInformationDesk.LinuxReleaseID.debian
        )

    @classmethod
    def _clean_ppas(
        cls, ppas: List[str], remove_software_properties_common: bool
    ) -> None:
        normalized_ppas = cls.normalize_ppas(ppas)

        for ppa in normalized_ppas:
            Invoker.invoke(command=f"add-apt-repository -y --remove {ppa}")

        if remove_software_properties_common:
            Invoker.invoke(
                command="apt-get -y purge software-properties-common --auto-remove"
            )

    @classmethod
    def _add_ppas(
        cls, ppas: List[str], update: bool, force_ppas_on_non_ubuntu: bool = False
    ) -> bool:
        software_properties_common_installed = False

        if not ppas:
            return software_properties_common_installed

        if not cls.is_ubuntu() and not force_ppas_on_non_ubuntu:
            raise cls.AptGetInstallerError(
                "in order to install ppas on non-ubuntu distros use the force-ppas-on-non-ubuntu flag"
            )

        normalized_ppas = cls.normalize_ppas(ppas)

        if (
            Invoker.invoke("dpkg -s software-properties-common", raise_on_failure=False)
            != 0
        ):
            Invoker.invoke(command="apt-get install -y software-properties-common")
            software_properties_common_installed = True

        for ppa in normalized_ppas:
            Invoker.invoke(command=f"add-apt-repository -y {ppa}")

        if update:
            Invoker.invoke(command="apt-get update -y")

        return software_properties_common_installed

    @classmethod
    def install(
        cls,
        packages: List[str],
        ppas: Optional[List[str]] = None,
        force_ppas_on_non_ubuntu: bool = False,
        clean_ppas: bool = True,
        clean_cache: bool = True,
        preserve_apt_list: bool = True,
    ) -> None:
        assert (
            cls.is_debian_like()
        ), "apt-get should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        software_properties_common_installed = False
        with tempfile.TemporaryDirectory() as tempdir:
            if preserve_apt_list:
                Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

            try:
                Invoker.invoke(command="apt-get update -y")

                if ppas:
                    software_properties_common_installed = cls._add_ppas(
                        ppas,
                        update=True,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                    )

                Invoker.invoke(
                    command=f"apt-get install -y --no-install-recommends {' '.join(packages)}"
                )

            finally:
                if ppas and clean_ppas:
                    cls._clean_ppas(
                        ppas=ppas,
                        remove_software_properties_common=software_properties_common_installed,
                    )

                if clean_cache:
                    Invoker.invoke(command="apt-get clean")

                if preserve_apt_list:
                    # Note: not using dir/* syntax as that doesnt work on 'sh' shell (alpine)
                    Invoker.invoke(
                        command=f"rm -r /var/lib/apt/lists && mv {tempdir} /var/lib/apt/lists"
                    )
