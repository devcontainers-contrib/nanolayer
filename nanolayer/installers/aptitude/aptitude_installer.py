import tempfile
from typing import Dict, List, Optional

from nanolayer.installers.apt_get.apt_get_installer import AptGetInstaller
from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class AptitudeInstaller:
    class InstallAptitude(Exception):
        pass

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

        if ppas and not cls.is_ubuntu() and not force_ppas_on_non_ubuntu:
            raise cls.PPASOnNonUbuntu()

        normalized_ppas = cls.normalize_ppas(ppas)
        software_properties_common_installed = False
        aptitude_installed = False

        with tempfile.TemporaryDirectory() as tempdir:
            try:
                if preserve_apt_list:
                    Invoker.invoke(
                        command=f"cp -p -R /var/lib/apt/lists {tempdir}",
                        raise_on_failure=True,
                        exception_class=cls.AptUpdateFailed,
                    )

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
                    if (
                        Invoker.invoke(
                            "dpkg -s software-properties-common", raise_on_failure=False
                        )
                        != 0
                    ):
                        Invoker.invoke(
                            command="apt-get install -y software-properties-common",
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
                        command="aptitude update -y",
                        raise_on_failure=True,
                        exception_class=cls.AptUpdateFailed,
                    )

                Invoker.invoke(
                    command=f"aptitude install -y {' '.join(packages)}",
                    raise_on_failure=True,
                    exception_class=cls.AptUpdateFailed,
                )

            finally:
                if clean_ppas:
                    for ppa in normalized_ppas:
                        Invoker.invoke(
                            command=f"add-apt-repository -y --remove {ppa}",
                            raise_on_failure=True,
                            exception_class=cls.RemovePPAsFailed,
                        )

                    if software_properties_common_installed:
                        Invoker.invoke(
                            command="apt-get -y purge software-properties-common --auto-remove",
                            raise_on_failure=True,
                            exception_class=cls.RemovePPAsFailed,
                        )

                if clean_cache:
                    Invoker.invoke(
                        command="aptitude clean",
                        raise_on_failure=True,
                        exception_class=cls.CleanUpFailed,
                    )

                if aptitude_installed and remove_installer_if_not_exists:
                    Invoker.invoke(
                        command="apt-get -y purge aptitude --auto-remove",
                        raise_on_failure=True,
                        exception_class=cls.CleanUpFailed,
                    )

                if preserve_apt_list:
                    Invoker.invoke(
                        command=f"mv {tempdir} /var/lib/apt/lists",
                        raise_on_failure=True,
                        exception_class=cls.CleanUpFailed,
                    )
