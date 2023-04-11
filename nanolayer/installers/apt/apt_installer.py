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
        clean_ppas: bool = True,
        clean_cache: bool = True,
        preserve_apt_list: bool = True,
    ) -> None:
        assert (
            cls.is_debian_like()
        ), "apt should be used on debian-like linux distribution (debian, ubuntu, raspian  etc)"

        software_properties_common_installed = False

        with tempfile.TemporaryDirectory() as tempdir:
            if preserve_apt_list:
                Invoker.invoke(command=f"cp -p -R /var/lib/apt/lists {tempdir}")

            try:
                Invoker.invoke(command="apt update -y")

                if ppas:
                    software_properties_common_installed = AptGetInstaller._add_ppas(
                        ppas=ppas,
                        update=True,
                        force_ppas_on_non_ubuntu=force_ppas_on_non_ubuntu,
                    )

                Invoker.invoke(
                    command=f"apt install -y --no-install-recommends {' '.join(packages)}"
                )

            finally:
                if clean_ppas:
                    AptGetInstaller._clean_ppas(
                        ppas=ppas,
                        remove_software_properties_common=software_properties_common_installed,
                    )

                if clean_cache:
                    Invoker.invoke(command="apt clean")
                if preserve_apt_list:
                    Invoker.invoke(command=f"mv {tempdir} /var/lib/apt/lists")
