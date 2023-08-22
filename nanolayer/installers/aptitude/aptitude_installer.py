import tempfile
from typing import Dict, List, Optional

from nanolayer.installers.apt_get.apt_get_installer import AptGetInstaller
from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class AptitudeInstaller:
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
        ), "aptitude should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        support_packages_installed: List[str] = []
        installed_ppas: List[str] = []
        aptitude_installed = False

        with tempfile.TemporaryDirectory() as tempdir:
            try:
                # preserving previuse cache
                Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

                Invoker.invoke(command="apt-get update -y")

                # ensure aptitude existance
                if Invoker.invoke("dpkg -s aptitude", raise_on_failure=False) != 0:
                    AptGetInstaller.install(
                        packages=["aptitude"],
                    )
                    aptitude_installed = True

                if ppas:
                    (
                        installed_ppas,
                        support_packages_installed,
                    ) = AptGetInstaller._add_ppas(
                        ppas=ppas,
                        update=True,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                    )

                Invoker.invoke(command=f"aptitude install -y {' '.join(packages)}")

            finally:
                AptGetInstaller._clean_ppas(
                    ppas=installed_ppas,
                    purge_packages=support_packages_installed,
                )

                Invoker.invoke(command="aptitude clean")

                if aptitude_installed:
                    Invoker.invoke(command="apt-get -y purge aptitude --auto-remove")

                # restore lists cache
                # Note: The reason for not using the dir/* syntax is because
                # that doesnt work on ash based shell (alpine)
                Invoker.invoke(
                    command=f"rm -r /var/lib/apt/lists && mv {tempdir}/lists /var/lib/apt/lists"
                )
