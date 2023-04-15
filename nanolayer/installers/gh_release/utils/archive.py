from tarfile import is_tarfile
from typing import Any, List
from zipfile import is_zipfile

from nanolayer.installers.gh_release.utils.tar_archive import TarArchive
from nanolayer.installers.gh_release.utils.zip_archive import ZipArchive


class Archive:
    def __enter__(self) -> None:
        return self._archive.__enter__()

    def __exit__(self, *args: Any, **kwargs: Any):
        return self._archive.__exit__(*args, **kwargs)

    @staticmethod
    def is_archive(name: str) -> bool:
        return is_tarfile(name) or is_zipfile(name)

    def get_member_permissions(self, member_name: str) -> int:
        return self._archive.get_member_permissions(member_name)

    def extract(self, member: str, path: str) -> None:
        self._archive.extract(member, path)

    def extractall(self, member: str) -> None:
        self._archive.extractall(
            member,
        )

    def __init__(self, name: str) -> None:
        if is_tarfile(name):
            self._archive = TarArchive.open(name=name)
        elif is_zipfile(name):
            self._archive = ZipArchive(name)
        else:
            raise ValueError(f"unsupported archive: {name}")

    def get_names_by_prefix(self, prefix: str) -> None:
        return self._archive.get_names_by_prefix(prefix)

    def get_names_by_suffix(self, suffix: str) -> None:
        return self._archive.get_names_by_suffix(suffix)

    def names_by_filename(self, filename: str) -> None:
        return self._archive.names_by_filename(filename)

    def get_file_members(self) -> List[str]:
        return self._archive.get_file_members()
