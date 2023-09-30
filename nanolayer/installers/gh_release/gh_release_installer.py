import logging
import os
import platform
import shutil
import tempfile
import urllib
from pathlib import Path
from typing import Dict, List, Optional, Union

from nanolayer.installers.gh_release.resolvers.asset_resolver import AssetResolver
from nanolayer.installers.gh_release.resolvers.binary_resolver import BinaryResolver
from nanolayer.installers.gh_release.resolvers.release_resolver import ReleaseResolver
from nanolayer.installers.gh_release.utils.archive import Archive
from nanolayer.utils.linux_information_desk import LinuxInformationDesk

logger = logging.getLogger(__name__)


class GHReleaseInstaller:
    DEFAULT_BIN_LOCATION = "/usr/local/bin"
    DEFAULT_LIB_LOCATION = "/usr/local/lib"

    BIN_PERMISSIONS = "755"

    SUPPORTED_ARCH = (
        LinuxInformationDesk.Architecture.ARM64.value,
        LinuxInformationDesk.Architecture.x86_64.value,
    )

    class GHReleaseInstallerError(Exception):
        pass

    @classmethod
    def _get_asset(cls, url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
        if not url.startswith("http"):
            raise ValueError("only http/https links are permited")

        if headers is None:
            headers = {}

        if "User-Agent" not in headers:
            headers["User-Agent"] = "nanolayer"

        request = urllib.request.Request(url=url, headers=headers)

        response = urllib.request.urlopen(request)  # nosec

        return response.read()

    @classmethod
    def _download_asset(cls, url: str, target: Path) -> None:
        target = Path(target)
        if target.exists():
            raise ValueError(f"{target} already exists.")

        target.parent.mkdir(parents=True, exist_ok=True)

        with open(target, "wb") as f:
            f.write(cls._get_asset(url))

    @classmethod
    def _resolve_and_validate_dir(
        cls, dir_location: Optional[Union[str, Path]], default: str
    ) -> Path:
        # todo: return based on linux distro

        if dir_location is None:
            dir_location = default

        if isinstance(dir_location, str):
            dir_location = Path(dir_location)

        assert (
            not dir_location.is_file()
        ), f"{dir_location} should be a folder - got file"

        dir_location.mkdir(parents=True, exist_ok=True)

        return dir_location

    @classmethod
    def _recursive_chmod(cls, dir_location: str, permissions: str) -> None:
        octal_permissions = int(permissions, base=8)
        os.chmod(dir_location, octal_permissions)
        if os.path.isdir(dir_location):
            for root, dirs, files in os.walk(dir_location):
                for f in files:
                    os.chmod(os.path.join(root, f), octal_permissions)
                for d in dirs:
                    os.chmod(os.path.join(root, d), octal_permissions)

    @classmethod
    def install(
        cls,
        repo: str,
        binary_names: List[str],
        lib_name: Optional[str] = None,
        bin_location: Optional[Union[str, Path]] = None,
        lib_location: Optional[Union[str, Path]] = None,
        asset_regex: Optional[str] = None,
        version: str = "latest",
        force: bool = False,
        release_tag_regex: Optional[str] = None,
        filter_assets_by_architecture: bool = True,
        filter_assets_by_platform: bool = True,
        filter_assets_by_misc: bool = True,
        filter_assets_by_bitness: bool = True,
    ) -> None:
        if lib_name is None or lib_name == "":
            if len(binary_names) > 1:
                raise ValueError(
                    "If multiple binary names given, lib name has to be given as well"
                )
            lib_name = binary_names[0]

        if "linux" not in platform.system().lower():
            raise ValueError(
                f"Currently only the Linux platform is supported (got {platform.system().lower()})"
            )

        # will raise an exception if bin_location is given and is not a directory
        bin_location = cls._resolve_and_validate_dir(
            bin_location, cls.DEFAULT_BIN_LOCATION
        )
        lib_location = cls._resolve_and_validate_dir(
            lib_location, cls.DEFAULT_LIB_LOCATION
        )

        final_binary_locations = []
        for binary_name in binary_names:
            final_binary_location = bin_location.joinpath(binary_name)
            if final_binary_location.exists() and not force:
                raise cls.GHReleaseInstallerError(
                    f"target {final_binary_location} already exists"
                )
            final_binary_locations.append(final_binary_location)

        # Will raise an exception if release for the requested version does not exists
        release_version = ReleaseResolver.resolve(
            asked_version=version, repo=repo, release_tag_regex=release_tag_regex
        )

        try:
            # will raise an exception if more or less than a single asset can meet the requirments
            resolved_asset = AssetResolver.resolve(
                repo=repo,
                release_version=release_version,
                asset_regex=asset_regex,
                binary_names=binary_names,
                filter_assets_by_architecture=filter_assets_by_architecture,
                filter_assets_by_bitness=filter_assets_by_bitness,
                filter_assets_by_platform=filter_assets_by_platform,
                filter_assets_by_misc=filter_assets_by_misc,
            )
        except AssetResolver.NoReleaseError as e:
            release_version = ReleaseResolver.resolve(
                asked_version=version,
                repo=repo,
                release_tag_regex=release_tag_regex,
                use_github_api=True,
            )
            # will raise an exception if more or less than a single asset can meet the requirments
            resolved_asset = AssetResolver.resolve(
                repo=repo,
                release_version=release_version,
                asset_regex=asset_regex,
                binary_names=binary_names,
                filter_assets_by_architecture=filter_assets_by_architecture,
                filter_assets_by_bitness=filter_assets_by_bitness,
                filter_assets_by_platform=filter_assets_by_platform,
                filter_assets_by_misc=filter_assets_by_misc,
            )

        logger.warning("resolved asset: %s", resolved_asset.name)

        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            temp_asset_path = tempdir.joinpath("temp_asset")
            temp_extraction_path = tempdir.joinpath("temp_extraction")
            cls._download_asset(
                url=resolved_asset.browser_download_url, target=temp_asset_path
            )
            if not Archive.is_archive(temp_asset_path):
                from nanolayer.installers.gh_release.utils.compressed_file import (
                    get_compressed_file,
                )

                compressed_file = get_compressed_file(temp_asset_path)
                if compressed_file is None:
                    logger.warning("asset recognized as a binary")

                    if len(binary_names) > 1:
                        raise cls.GHReleaseInstallerError(
                            "multiple binary names given but the resolved asset is a single binary file"
                        )

                    # assumes regular binary
                    shutil.copyfile(temp_asset_path, final_binary_locations[0])
                else:
                    logger.warning(
                        "asset recognized as a %s file", compressed_file.mime_type
                    )
                    with open(final_binary_locations[0], "wb") as f:
                        f.write(compressed_file.accessor.read())

                cls._recursive_chmod(final_binary_locations[0], cls.BIN_PERMISSIONS)

            else:
                logger.warning("asset recognized as an archive file")

                archive_member_names = BinaryResolver.resolve(
                    temp_asset_path, binary_names
                )
                assert len(archive_member_names) == len(
                    binary_names
                ), "amount of resolved archive members does not match the amount of binary names gived"
                logger.warning(
                    "binary members found in archive are: %s", str(archive_member_names)
                )

                with Archive(temp_asset_path) as archive_file:
                    if len(archive_file.get_file_members()) > len(binary_names):
                        logger.warning(
                            "archive recognized as library (contains additional files outside of requested binaries)"
                        )
                        # In case other files in same dir, assume lib dir.
                        # extracting to lib location and soft link the target into bin location
                        target_lib_location = lib_location.joinpath(lib_name)

                        logger.warning(
                            "extracting %s into %s",
                            resolved_asset.name,
                            target_lib_location,
                        )

                        if target_lib_location.exists() and not force:
                            raise cls.GHReleaseInstallerError(
                                f"{target_lib_location} already exists"
                            )

                        archive_file.extractall(temp_extraction_path)

                        try:
                            shutil.copytree(
                                temp_extraction_path,
                                target_lib_location,
                                dirs_exist_ok=force,
                            )
                        except FileExistsError as exc:
                            raise cls.GHReleaseInstallerError(
                                f"{target_lib_location} already exists"
                            ) from exc

                        # execute permissions
                        cls._recursive_chmod(target_lib_location, cls.BIN_PERMISSIONS)
                        for (
                            binary_name,
                            final_binary_location,
                            archive_member_name,
                        ) in zip(
                            binary_names, final_binary_locations, archive_member_names
                        ):
                            lib_binary_location = target_lib_location.joinpath(
                                archive_member_name
                            )
                            logger.warning(
                                "linking %s to %s",
                                lib_binary_location,
                                final_binary_location,
                            )
                            try:
                                os.symlink(lib_binary_location, final_binary_location)
                            except FileExistsError:
                                os.remove(final_binary_location)
                                os.symlink(lib_binary_location, final_binary_location)
                    else:
                        for (
                            binary_name,
                            final_binary_location,
                            archive_member_name,
                        ) in zip(
                            binary_names, final_binary_locations, archive_member_names
                        ):
                            # In case of a single file, copy it into bin location and rename it as the target name
                            archive_file.extract(
                                archive_member_name, temp_extraction_path
                            )
                            if archive_member_name != binary_name:
                                logger.warning(
                                    "renaming %s to %s",
                                    archive_member_name,
                                    binary_name,
                                )
                            shutil.copyfile(
                                temp_extraction_path.joinpath(archive_member_name),
                                final_binary_location,
                            )
                            cls._recursive_chmod(
                                final_binary_location, cls.BIN_PERMISSIONS
                            )
