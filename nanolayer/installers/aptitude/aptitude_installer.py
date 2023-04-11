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
        clean_ppas: bool = True,
        clean_cache: bool = True,
        preserve_apt_list: bool = True,
        remove_installer_if_not_exists: bool = True,
    ) -> None:
        assert (
            cls.is_debian_like()
        ), "aptitude should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        software_properties_common_installed = False
        aptitude_installed = False

        with tempfile.TemporaryDirectory() as tempdir:
            try:
                if preserve_apt_list:
                    Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

                # ensure aptitude existance
                if Invoker.invoke("dpkg -s aptitude", raise_on_failure=False) != 0:
                    AptGetInstaller.install(
                        packages=["aptitude"],
                        ppas=ppas,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                        clean_ppas=clean_ppas,
                        clean_cache=clean_cache,
                        preserve_apt_list=preserve_apt_list,
                    )
                    aptitude_installed = True

                if ppas:
                    software_properties_common_installed = AptGetInstaller._add_ppas(
                        ppas=ppas,
                        update=True,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                    )

                Invoker.invoke(command=f"aptitude install -y {' '.join(packages)}")

            finally:
                if clean_ppas:
                    AptGetInstaller._clean_ppas(
                        ppas=ppas,
                        remove_software_properties_common=software_properties_common_installed,
                    )

                if clean_cache:
                    Invoker.invoke(command="aptitude clean")

                if aptitude_installed and remove_installer_if_not_exists:
                    Invoker.invoke(command="apt-get -y purge aptitude --auto-remove")

                if preserve_apt_list:
                    Invoker.invoke(command=f"mv {tempdir} /var/lib/apt/lists")
