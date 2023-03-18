import os
from enum import Enum
from typing import Dict


class LinuxInformationDesk:

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
    def get_release_id(cls, id_like: bool = False) ->'LinuxInformationDesk.LinuxReleaseID':
        assert cls.has_root_privileges()

        def _parse_env_file(path: str) -> Dict[str,str]:
            with open(path, 'r') as f:                                               
                return dict(tuple(line.replace('\n', '').split('=')) for line in f.readlines() if not line.startswith('#'))
        
        parsed_os_release = _parse_env_file("/etc/os-release")

        if id_like:
            os_release_id = parsed_os_release.get('ID_LIKE', None).lower()
            if os_release_id is None:
                os_release_id = parsed_os_release['ID'].lower()
        else:
            os_release_id = parsed_os_release['ID'].lower()

        if "ubuntu" in os_release_id:
            return cls.LinuxReleaseID.ubuntu
        elif "debian" in os_release_id:
            return cls.LinuxReleaseID.debian
        elif "alpine" in os_release_id:
            return cls.LinuxReleaseID.alpine
        elif "fedora" in os_release_id :
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
