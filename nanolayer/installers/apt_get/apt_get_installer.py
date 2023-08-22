import tempfile
import warnings
from typing import List, Optional, Tuple

from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class AptGetInstaller:
    PPA_SUPPORT_PACKAGES = ("software-properties-common",)
    PPA_SUPPORT_PACKAGES_DEBIAN = ("python3-launchpadlib",)

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
        cls, ppas: List[str], purge_packages: Optional[List[str]] = None
    ) -> None:
        normalized_ppas = cls.normalize_ppas(ppas)

        for ppa in normalized_ppas:
            Invoker.invoke(command=f"add-apt-repository -y --remove {ppa}")

        if purge_packages is not None:
            for package in purge_packages:
                Invoker.invoke(command=f"apt-get -y purge {package} --auto-remove")

    @classmethod
    def _add_ppas(
        cls,
        ppas: Optional[List[str]] = None,
        update: bool = True,
        force_ppas_on_non_ubuntu: bool = False,
    ) -> Tuple[List[str], List[str]]:
        installed_ppas: List[str] = []

        installed_ppa_support_packages: List[str] = []

        if ppas is None:
            ppas = []

        if ppas and not cls.is_ubuntu() and not force_ppas_on_non_ubuntu:
            warnings.warn(
                "ppas are ignored on non-ubuntu distros!\n in order to include them anyway use the --force-ppas-on-non-ubuntu flag"
            )
            ppas = []

        if not ppas:
            return [], installed_ppa_support_packages

        normalized_ppas = cls.normalize_ppas(ppas)

        required_ppa_support_package = (
            cls.PPA_SUPPORT_PACKAGES
            if cls.is_ubuntu()
            else cls.PPA_SUPPORT_PACKAGES + cls.PPA_SUPPORT_PACKAGES_DEBIAN
        )

        for ppa_support_package in required_ppa_support_package:
            if (
                Invoker.invoke(f"dpkg -s {ppa_support_package}", raise_on_failure=False)
                != 0
            ):
                Invoker.invoke(command=f"apt-get install -y {ppa_support_package}")
                installed_ppa_support_packages.append(ppa_support_package)

        for ppa in normalized_ppas:
            Invoker.invoke(command=f"add-apt-repository -y {ppa}")
            installed_ppas.append(ppa)

        if update:
            Invoker.invoke(command="apt-get update -y")

        return installed_ppas, installed_ppa_support_packages

    @classmethod
    def install(
        cls,
        packages: List[str],
        ppas: Optional[List[str]] = None,
        force_ppas_on_non_ubuntu: bool = False,
    ) -> None:
        if ppas is None:
            ppas = []

        assert (
            cls.is_debian_like()
        ), "apt-get should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        support_packages_installed: List[str] = []
        installed_ppas: List[str] = []

        with tempfile.TemporaryDirectory() as tempdir:
            # preserving previuse cache
            Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

            try:
                Invoker.invoke(command="apt-get update -y")

                installed_ppas, support_packages_installed = cls._add_ppas(
                    ppas, update=True, force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu
                )

                Invoker.invoke(
                    command=f"apt-get install -y --no-install-recommends {' '.join(packages)}"
                )

            finally:
                # remove ppa indexes
                cls._clean_ppas(
                    ppas=installed_ppas,
                    purge_packages=support_packages_installed,
                )

                # remove archives cache
                Invoker.invoke(command="apt-get clean")

                # restore lists cache
                # Note: The reason for not using the dir/* syntax is because
                # that doesnt work on ash based shell (alpine)
                Invoker.invoke(
                    command=f"rm -r /var/lib/apt/lists && mv {tempdir}/lists /var/lib/apt/lists"
                )
