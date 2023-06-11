import os
import platform
from enum import Enum
from typing import Dict


class EnvFile:
    @staticmethod
    def parse(path: str) -> Dict[str, str]:
        with open(path, "r") as f:
            return dict(
                tuple(line.replace("\n", "").split("="))
                for line in f.readlines()
                if not line.startswith("#")
            )


class ProcFile:
    @staticmethod
    def parse(path: str) -> Dict[str, str]:
        items = {}
        with open(path, "r") as f:
            for line in f.readlines():
                splitted_values = line.split(":")
                if len(splitted_values) == 2:
                    items[splitted_values[0].strip()] = splitted_values[1].strip()
        return items


class LinuxInformationDesk:
    OS_RELEASE_PATH = "/etc/os-release"

    class Bitness(Enum):
        B32BIT = "32bit"
        B64BIT = "64bit"

    class Architecture(Enum):
        ARM64 = "arm64"
        x86_64 = "x86_64"
        ARMV5 = "armv5"
        ARMV6 = "armv6"
        ARMV7 = "armv7"
        ARMHF = "armhf"
        ARM32 = "arm32"
        I386 = "i386"
        I686 = "i686"
        PPC64 = "ppc64"
        S390 = "s390"
        OTHER = "other"

    @classmethod
    def get_architecture(cls) -> "LinuxInformationDesk.Architecture":
        architecture = platform.machine().lower()
        if "x86_64" in architecture or "amd64" in architecture:
            return cls.Architecture.x86_64
        if "arm64" in architecture or "aarch64" in architecture:
            return cls.Architecture.ARM64
        if "armv5" in architecture:
            return cls.Architecture.ARMV5
        if "armv6" in architecture:
            return cls.Architecture.ARMV6
        if "armv7" in architecture:
            return cls.Architecture.ARMV7
        if "armhf" in architecture:
            return cls.Architecture.ARMHF
        if "i386" in architecture:
            return cls.Architecture.I386
        if "i686" in architecture:
            return cls.Architecture.I686
        if "ppc" in architecture:
            return cls.Architecture.PPC64
        if "arm32" in architecture:
            return cls.Architecture.ARM32
        if "s390" in architecture:
            return cls.Architecture.S390
        else:
            return cls.Architecture.OTHER

    class LinuxReleaseID(Enum):
        ubuntu: str = "ubuntu"
        debian: str = "debian"
        alpine: str = "alpine"
        rhel: str = "rhel"
        fedora: str = "fedora"
        opensuse: str = "opensuse"
        raspbian: str = "raspbian"
        manjaro: str = "manjaro"
        arch: str = "arch"

    @classmethod
    def _get_release_id_str(cls, id_like: bool = False) -> str:
        assert cls.has_root_privileges()

        parsed_os_release = EnvFile.parse(cls.OS_RELEASE_PATH)

        if id_like:
            os_release_id = parsed_os_release.get("ID_LIKE", None)
            if os_release_id is None:
                os_release_id = parsed_os_release["ID"]
        else:
            os_release_id = parsed_os_release["ID"]

        return os_release_id

    @classmethod
    def get_bitness(cls) -> "LinuxInformationDesk.Bitness":
        bitness = platform.architecture()[0]

        if "32" in bitness:
            return cls.Bitness.B32BIT
        elif "64" in bitness:
            return cls.Bitness.B64BIT
        else:
            raise ValueError(f"could not resolve bitness: {bitness}")

    @classmethod
    def get_release_id(
        cls, id_like: bool = False
    ) -> "LinuxInformationDesk.LinuxReleaseID":
        assert cls.has_root_privileges()

        os_release_id = cls._get_release_id_str(id_like=id_like).lower()

        if "ubuntu" in os_release_id:
            return cls.LinuxReleaseID.ubuntu
        elif "debian" in os_release_id:
            return cls.LinuxReleaseID.debian
        elif "alpine" in os_release_id:
            return cls.LinuxReleaseID.alpine
        elif "fedora" in os_release_id:
            return cls.LinuxReleaseID.fedora
        elif "opensuse" in os_release_id:
            return cls.LinuxReleaseID.opensuse
        elif "rhel" in os_release_id:
            return cls.LinuxReleaseID.rhel
        elif "raspbian" in os_release_id:
            return cls.LinuxReleaseID.raspbian

    @staticmethod
    def has_root_privileges() -> bool:
        # credit: https://stackoverflow.com/a/69134255/5922329
        return os.environ.get("SUDO_UID") or os.geteuid() == 0
