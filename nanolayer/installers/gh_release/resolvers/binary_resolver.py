import stat
from typing import List

from nanolayer.installers.gh_release.utils.archive import Archive


class BinaryResolver:
    class IsExecutableFilter:
        @staticmethod
        def _is_owner_executable(permissions: int) -> bool:
            return permissions & stat.S_IEXEC != 0

        @staticmethod
        def _is_group_executable(permissions: int) -> bool:
            return permissions & stat.S_IXGRP != 0

        @staticmethod
        def _is_user_executable(permissions: int) -> bool:
            return permissions & stat.S_IXOTH != 0

        def __init__(self, archive: Archive) -> None:
            self.archive = archive

        def __call__(self, member: str) -> bool:
            permissions = self.archive.get_member_permissions(member)
            return (
                self._is_owner_executable(permissions)
                or self._is_group_executable(permissions)
                or self._is_user_executable(permissions)
            )

    class BinaryResolverError(Exception):
        pass

    @classmethod
    def resolve(cls, archive_path: str, binary_names: List[str]) -> List[str]:
        binary_members = []
        with Archive(archive_path) as archive_file:
            # resolve target member name
            if len(archive_file.get_file_members()) == 1:
                if len(binary_names) > 1:
                    raise cls.BinaryResolverError(
                        f"multiple binary names given, but only one member in archive: {archive_file.get_file_members()[0]}"
                    )

                # In case of a single member, use it no matter how its named
                binary_members.append(archive_file.get_file_members()[0])
            else:
                for binary_name in binary_names:
                    target_member_names = archive_file.names_by_filename(binary_name)
                    if len(target_member_names) > 1:
                        # try narrow it down to single binary using filters
                        filtered_target_member_names = list(
                            filter(
                                cls.IsExecutableFilter(archive_file),
                                target_member_names,
                            )
                        )

                        if len(filtered_target_member_names) != 1:
                            raise cls.BinaryResolverError(
                                f"multiple binary matches were found in archive: {target_member_names}"
                            )
                    if len(target_member_names) == 0:
                        raise cls.BinaryResolverError(
                            f"no binary named {binary_name} found in archive"
                        )
                    binary_members.append(target_member_names[0])

            return binary_members
