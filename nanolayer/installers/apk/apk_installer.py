import tempfile
from typing import List

from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk


class ApkInstaller:
    @classmethod
    def is_alpine(cls) -> bool:
        return (
            LinuxInformationDesk.get_release_id()
            == LinuxInformationDesk.LinuxReleaseID.alpine
        )

    @classmethod
    def delete(cls, packages: List[str]) -> None:
        assert cls.is_alpine(), "apk should be used on alpine linux distribution"
        Invoker.invoke(command=f"apk del {' '.join(packages)}")

    @classmethod
    def install(
        cls,
        packages: List[str],
    ) -> None:
        assert cls.is_alpine(), "apk should be used on alpine linux distribution"

        with tempfile.TemporaryDirectory() as tempdir:
            Invoker.invoke(command=f"cp -p -R /var/cache/apk {tempdir}")

            try:
                Invoker.invoke(command="apk update")

                Invoker.invoke(command=f"apk add --no-cache {' '.join(packages)}")

            finally:
                # Note: not using dir/* syntax as that doesnt work on 'sh' shell (alpine)
                Invoker.invoke(
                    command=f"rm -r /var/cache/apk && mv {tempdir}/apk /var/cache/apk"
                )
