from typing import List
from zipfile import ZipFile

from nanolayer.installers.gh_release.utils.abstract_archive import (
    AbstractExtendedArchive,
)


class ZipArchive(ZipFile, AbstractExtendedArchive):
    class ZipArchiveError(Exception):
        pass

    def get_member_permissions(self, member_name: str) -> int:
        return int((oct(self.getinfo(member_name).external_attr >> 16)), base=8)

    def get_file_members(self) -> List[str]:
        members = self.namelist()
        return [member for member in members if not member.endswith("/")]

    def get_names_by_prefix(self, prefix: str) -> None:
        subdir_and_files = [
            name for name in self.get_file_members() if name.startswith(prefix)
        ]
        return subdir_and_files

    def get_names_by_suffix(self, suffix: str) -> None:
        subdir_and_files = [
            name for name in self.get_file_members() if name.endswith(suffix)
        ]
        return subdir_and_files

    def names_by_filename(self, filename: str) -> List[str]:
        matching_members = self.get_names_by_suffix(suffix=f"/{filename}")
        # could also be as root member
        if filename in self.get_file_members():
            matching_members.append(filename)

        return matching_members
