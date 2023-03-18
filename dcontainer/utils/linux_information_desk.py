import os
from enum import Enum
from typing import Dict


class LinuxDistroEnum(Enum):
    ubuntu: str = "ubuntu"
    debian: str = "debian"
    alpine: str = "alpine"
    redhat: str = "redhat"
    fedora: str = "fedora"
    open_suse: str = "open_suse"


class LinuxInformationDesk:

    def get_distro() ->LinuxDistroEnum:
         
        def _parse_env_file(path: str) -> Dict[str,str]:
            with open(path, 'r') as f:                                               
                return dict(tuple(line.replace('\n', '').split('=')) for line in f.readlines() if not line.startswith('#'))
        
        parsed_os_release = cls._parse_env_file("/etc/os-release")

        os_release_name = parsed_os_release['NAME']

        if "ubuntu" in os_release_name.lower():
            return LinuxDistroEnum.ubuntu
        elif "debian" in os_release_name.lower():
            return LinuxDistroEnum.debian
        

    @classmethod
    def is_ubuntu(cls) -> bool:
        Invoker.check_root_privileges()
        parsed_os_release = cls._parse_env_file("/etc/os-release")
        return "ubuntu" in parsed_os_release['NAME'].lower()
    


    def has_root_privileges() -> bool:
        # credit: https://stackoverflow.com/a/69134255/5922329
        return os.environ.get("SUDO_UID") or os.geteuid() == 0
