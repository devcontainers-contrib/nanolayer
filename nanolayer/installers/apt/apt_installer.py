import tempfile
from typing import Dict, List, Optional

from nanolayer.installers.apt_get.apt_get_installer import AptGetInstaller
from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class AptInstaller:
    @staticmethod
    def _parse_env_file(path: str) -> Dict[str, str]:
        with open(path, "r") as f:
            return dict(
                tuple(line.replace("\n", "").split("="))
                for line in f.readlines()
                if not line.startswith("#")
            )

    @classmethod
    def is_debian_like(cls) -> bool:
        return (
            LinuxInformationDesk.get_release_id(id_like=True)
            == LinuxInformationDesk.LinuxReleaseID.debian
        )

    @classmethod
    def install(
        cls,
        packages: List[str],
        ppas: Optional[List[str]] = None,
        force_ppas_on_non_ubuntu: bool = False,
    ) -> None:
        assert (
            cls.is_debian_like()
        ), "apt should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        support_packages_installed: List[str] = []
        installed_ppas: List[str] = []

        with tempfile.TemporaryDirectory() as tempdir:
            # preserving previuse cache
            Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

            try:
                Invoker.invoke(command="apt update -y")

                if ppas:
                    (
                        installed_ppas,
                        support_packages_installed,
                    ) = AptGetInstaller._add_ppas(
                        ppas=ppas,
                        update=True,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                    )

                Invoker.invoke(
                    command=f"apt install -y --no-install-recommends {' '.join(packages)}"
                )

            finally:
                # remove ppa indexes
                AptGetInstaller._clean_ppas(
                    ppas=installed_ppas,
                    purge_packages=support_packages_installed,
                )

                # remove archives cache
                Invoker.invoke(command="apt clean")

                # restore lists cache
                # Note: The reason for not using the dir/* syntax is because
                # that doesnt work on ash based shell (alpine)
                Invoker.invoke(
                    command=f"rm -r /var/lib/apt/lists && mv {tempdir}/lists /var/lib/apt/lists"
                )
