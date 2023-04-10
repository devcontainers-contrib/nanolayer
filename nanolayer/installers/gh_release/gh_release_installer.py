import json
import logging
import os
import platform
import re
import shutil
import tarfile
import tempfile
import urllib
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import invoke
import semver
from pydantic import BaseModel, Extra

from nanolayer.utils.invoker import Invoker
from nanolayer.utils.linux_information_desk import LinuxInformationDesk

logger = logging.getLogger(__name__)
from abc import ABC, abstractmethod
from tarfile import TarFile, is_tarfile
from zipfile import ZipFile, is_zipfile


class AbstractExtendedArchive(ABC):
    @abstractmethod
    def get_names_by_prefix(self, prefix: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_names_by_suffix(self, suffix: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def names_by_filename(self, filename: str) -> List[str]:
        raise NotImplementedError()

    @abstractmethod
    def get_file_members(self) -> List[str]:
        raise NotImplementedError()


class ExtendedZipFile(ZipFile, AbstractExtendedArchive):
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


class ExtendedTarFile(TarFile, AbstractExtendedArchive):
    def get_file_members(self) -> List[str]:
        members = self.getmembers()
        return [member.name for member in members if member.isfile()]

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


class Archive:
    def __enter__(self) -> None:
        return self._archive.__enter__()

    def __exit__(self, *args: Any, **kwargs: Any):
        return self._archive.__exit__(*args, **kwargs)

    @staticmethod
    def is_archive(name: str) -> bool:
        return is_tarfile(name) or is_zipfile(name)

    def extract(self, member: str, path: str) -> None:
        self._archive.extract(member, path)

    def extractall(self, member: str) -> None:
        self._archive.extractall(
            member,
        )

    def __init__(self, name: str) -> None:
        if is_tarfile(name):
            self._archive = ExtendedTarFile.open(name)
        elif is_zipfile(name):
            self._archive = ExtendedZipFile(name)
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


class PlatformType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


PLATFORM_REGEX_MAP = {
    PlatformType.WINDOWS: "(windows|Windows|WINDOWS|win32|-win-|\.msi$|.msixbundle$|\.exe$)",
    PlatformType.LINUX: "([Ll]inux)",
    PlatformType.MACOS: "(macOS|mac-os|-osx-|_osx_|[Dd]arwin)",
}


ARCH_REGEX_MAP = {
    LinuxInformationDesk.Architecture.ARMV6: "([Aa]rmv6)",
    LinuxInformationDesk.Architecture.ARMV7: "([Aa]rmv7)",
    LinuxInformationDesk.Architecture.ARMHF: "([Aa]rmhf)",
    LinuxInformationDesk.Architecture.I386: "(i386|-386|_386)",
    LinuxInformationDesk.Architecture.ARM32: "([Aa]rm32)",
    LinuxInformationDesk.Architecture.ARM64: "([Aa]rm64)",
    LinuxInformationDesk.Architecture.S390: "(s390x|s390)",
    LinuxInformationDesk.Architecture.PPC64: "(-ppc|ppc64|_ppc)",
    LinuxInformationDesk.Architecture.x86_64: "([Aa]md64|-x64|_x64|x86[_-]64)",
}


MISC_REGEX_MAP = {
    "packages": "(\.deb|\.rpm|\.pkg|\.apk)",
    "checksums": "(\.pub$|\.sig$|\.text$|\.txt$|[Cc]hecksums|sha256)",
}


class GHReleaseInstaller:
    class FindAllRegexFilter:
        def __init__(self, name: str, regex: str, negative: bool) -> None:
            self.name = name
            self.regex = regex
            self.negative = negative

        def __call__(self, asset: "GHReleaseInstaller.ReleaseAsset") -> bool:
            matches = len(re.findall(self.regex, asset.name))
            if self.negative:
                return matches == 0
            else:
                return matches > 0

    X86_X64_REGEX = ""
    ARM_REGEX = ""
    X64_APPLE_REGEX = ""
    ARM_APPLE_REGEX = ""

    DEFAULT_BIN_LOCATION = "/usr/local/bin"
    DEFAULT_LIB_LOCATION = "/usr/local/lib"

    BIN_PERMISSIONS = "755"

    SUPPORTED_ARCH = (
        LinuxInformationDesk.Architecture.ARM64.value,
        LinuxInformationDesk.Architecture.x86_64.value,
    )

    class ReleaseAsset(BaseModel):
        class Config:
            extra = Extra.ignore

        name: str
        browser_download_url: str
        label: Optional[str] = None
        size: int

    GIT_VERSION_TAG_REGEX = "(?:tags\/)(v)?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+)?$"

    class TooManyAssetsFound(Exception):
        pass

    class NoAssetsFound(Exception):
        pass

    class BadArchitecture(Exception):
        pass

    class NoPremissions(PermissionError):
        pass

    class BadPlatform(PermissionError):
        pass

    class ReleaseVersionNotFound(Exception):
        pass

    class MoBinaryMatchesFound(Exception):
        pass

    class MultipleBinaryMatchesFound(Exception):
        pass

    class TargetExists(Exception):
        pass

    class AddPPAsFailed(Invoker.InvokerException):
        pass

    class RemovePPAsFailed(Invoker.InvokerException):
        pass

    class CleanUpFailed(Invoker.InvokerException):
        pass

    @classmethod
    def get_version_tags(cls, repo: str) -> List[str]:
        response = invoke.run(
            f"git ls-remote --tags https://github.com/{repo}", pty=True, hide=True
        )
        if response.ok:
            matches = [
                re.findall(cls.GIT_VERSION_TAG_REGEX, line.strip())
                for line in response.stdout.split("\n")
            ]
        return [
            match[0][0] + ".".join(match[0][1:-1]) + match[0][-1]
            for match in matches
            if len(match) == 1
        ]

    @classmethod
    def get_latest_stable_version(cls, repo: str) -> List[str]:
        all_version_tags = cls.get_version_tags(repo)

        def strip_prefix(value: str, prefix: str) -> str:
            if value[: len(prefix)] == prefix:
                return value[len(prefix) :]
            return value

        semversions = [
            semver.VersionInfo.parse(strip_prefix(version, "v"))
            if semver.VersionInfo.isvalid(strip_prefix(version, "v"))
            else semver.VersionInfo(0, 0, 0)
            for version in all_version_tags
        ]

        sorted_tuples = sorted(
            zip(semversions, all_version_tags), key=lambda pair: pair[0]
        )

        stable_semversions = list(
            filter(
                lambda version_tuple: version_tuple[0].build is None
                and version_tuple[0].prerelease is None,
                sorted_tuples,
            )
        )

        return str(stable_semversions[-1][1])

    @classmethod
    def _get_release_by_tag(cls, repo: str, tag: str) -> Dict[str, Any]:
        response = urllib.request.urlopen(
            f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        )  # nosec
        return json.loads(response.read())

    @classmethod
    def _get_assets_by_tag(
        cls, repo: str, tag: str
    ) -> List["GHReleaseInstaller.ReleaseAsset"]:
        release_dict = cls._get_release_by_tag(repo=repo, tag=tag)
        return [cls.ReleaseAsset.parse_obj(asset) for asset in release_dict["assets"]]

    @classmethod
    def get_asset(cls, url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
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
    def download_asset(cls, url: str, target: Path) -> None:
        target = Path(target)
        if target.exists():
            raise ValueError(f"{target} already exists.")

        target.parent.mkdir(parents=True, exist_ok=True)

        with open(target, "wb") as f:
            f.write(cls.get_asset(url))

    @classmethod
    def resolve_release_version(cls, asked_version: str, repo: str) -> str:
        if asked_version == "latest":
            return cls.get_latest_stable_version(repo)
        else:
            versions = cls.get_version_tags(repo)
            if asked_version in versions:
                return asked_version

            elif f"v{asked_version}" in versions:
                return f"v{asked_version}"

            else:
                raise cls.ReleaseVersionNotFound(
                    f"Could not find a release version: {asked_version}"
                )

    @classmethod
    def resolve_asset(
        cls,
        repo: str,
        tag: str,
        target_name: str,
        asset_regex: Optional[str] = None,
        arch: Optional[LinuxInformationDesk.Architecture] = None,
    ) -> "GHReleaseInstaller.ReleaseAsset":
        assert not (
            asset_regex is None and arch is None
        ), "at least one of 'asset_regex','arch' arguments must be given"

        assets = cls._get_assets_by_tag(repo=repo, tag=tag)
        if asset_regex is not None:
            assets = list(
                filter(
                    lambda asset: re.match(asset_regex, asset.name) is not None, assets
                )
            )
            if len(assets) == 0:
                raise cls.NoAssetsFound(
                    f"no matches found for asset regex: {asset_regex}"
                )
            elif len(assets) >= 2:
                raise cls.NoAssetsFound(
                    f"More than one match was found for asset regex: {asset_regex}\n {assets}\n Please narrow down the asset regex"
                )
            else:
                return assets[0]
        else:
            # add all non-requested architecture as a negative filters
            bad_architecture_regexes = deepcopy(ARCH_REGEX_MAP)
            bad_architecture_regexes.pop(arch)
            negative_architecture_filters = [
                cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
                for name, regex in bad_architecture_regexes.items()
            ]

            # add misc files like checksums and packages as negative filters
            negative_misc_filters = [
                cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
                for name, regex in MISC_REGEX_MAP.items()
            ]

            # add all non-current platform as a negative filters
            bad_platform_regexes = deepcopy(PLATFORM_REGEX_MAP)
            bad_platform_regexes.pop(PlatformType.LINUX)
            negative_platform_filters = [
                cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
                for name, regex in bad_platform_regexes.items()
            ]

            # One filter to rule them all
            assets = filter(
                lambda asset: all(
                    f(asset)
                    for f in (
                        negative_architecture_filters
                        + negative_misc_filters
                        + negative_platform_filters
                    )
                ),
                assets,
            )

            # actually run the filters...
            assets = list(assets)

            if len(assets) == 1:
                return assets[0]
            elif len(assets) == 0:
                raise cls.NoAssetsFound("No matches found")

            # positive filters are being run one by one, because we want to discard those
            # who filter out all of the remaining.

            positive_filters = [
                cls.FindAllRegexFilter(
                    name=arch.value, regex=ARCH_REGEX_MAP[arch], negative=False
                ),
                cls.FindAllRegexFilter(
                    name=PlatformType.LINUX.value,
                    regex=PLATFORM_REGEX_MAP[PlatformType.LINUX],
                    negative=False,
                ),
                cls.FindAllRegexFilter(
                    name="contains target name",
                    regex=f".*{target_name}.*",
                    negative=False,
                ),
                cls.FindAllRegexFilter(
                    name="prefer musl",  # musl is compatible across more distros
                    regex=f".*musl.*",
                    negative=False,
                ),
            ]

            for positive_filter in positive_filters:
                filtered_assets = list(filter(positive_filter, assets))

                if len(filtered_assets) == 0:
                    # filter is too aggressive. ignoring it
                    continue
                else:
                    assets = filtered_assets

            if len(assets) > 1:
                raise cls.TooManyAssetsFound(f"Too many matches found: {assets}")

            return assets[0]

    @classmethod
    def resolve_and_validate_dir(
        cls, dir_location: Optional[Union[str, Path]], default: str
    ) -> Path:
        # todo: return based on linux distro

        if dir_location is None:
            dir_location = default

        if isinstance(dir_location, str):
            dir_location = Path(dir_location)

        assert dir_location.is_dir()

        return dir_location

    @classmethod
    def resolve_and_validate_architecture(
        cls, arch: Optional[Union[str, LinuxInformationDesk.Architecture]] = None
    ) -> Path:
        # todo: return based on linux distro
        if isinstance(arch, str):
            try:
                arch = LinuxInformationDesk.Architecture(arch.lower())
            except ValueError:
                raise cls.BadArchitecture(
                    f"architecture {arch} is not supported. (supported architectures are: {cls.SUPPORTED_ARCH})"
                )
        if arch is None:
            arch = LinuxInformationDesk.get_architecture()

        if arch.value not in cls.SUPPORTED_ARCH:
            raise cls.BadArchitecture(
                f"architecture {platform.machine()} is currently not supported. (supported architectures are: {cls.SUPPORTED_ARCH})"
            )

        return arch

    @classmethod
    def resolve_lib_location(cls) -> str:
        # todo: return based on linux distro
        return "/usr/local/lib"

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
        target_name: str,
        bin_location: Optional[Union[str, Path]] = None,
        lib_location: Optional[Union[str, Path]] = None,
        asset_regex: Optional[str] = None,
        version: str = "latest",
        force: bool = False,
        arch: Optional[str] = None,
    ) -> None:
        if "linux" not in platform.system().lower():
            raise cls.BadPlatform(
                f"Currently only the Linux platform is supported (got {platform.system().lower()})"
            )

        if not LinuxInformationDesk.has_root_privileges():
            raise cls.NoPremissions("Please run as root or with sudo")

        # will raise an exception if arch is invalid
        arch = cls.resolve_and_validate_architecture(arch)

        # will raise an exception if bin_location is given and is not a directory
        bin_location = cls.resolve_and_validate_dir(
            bin_location, cls.DEFAULT_BIN_LOCATION
        )
        lib_location = cls.resolve_and_validate_dir(
            lib_location, cls.DEFAULT_LIB_LOCATION
        )

        final_binary_location = bin_location.joinpath(target_name)
        if final_binary_location.exists() and not force:
            raise cls.TargetExists(f"target {final_binary_location} already exists")

        # Will raise an exception if release for the requested version does not exists
        version = cls.resolve_release_version(asked_version=version, repo=repo)

        # will raise an exception if more or less than a single asset can meet the requirments
        resolved_asset = cls.resolve_asset(
            repo=repo,
            tag=version,
            asset_regex=asset_regex,
            arch=arch,
            target_name=target_name,
        )

        logger.warning("resolved asset: %s", resolved_asset.name)

        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            temp_asset_path = tempdir.joinpath("temp_asset")
            temp_extraction_path = tempdir.joinpath("temp_extraction")
            cls.download_asset(
                url=resolved_asset.browser_download_url, target=temp_asset_path
            )

            if Archive.is_archive(temp_asset_path):
                with Archive(temp_asset_path) as archive_file:
                    logger.warning("asset recognized as an archive file")

                    # resolve target member name
                    if len(archive_file.get_file_members()) == 1:
                        # In case of a single member, use it no matter how its named
                        target_member_name = archive_file.get_file_members()[0]
                    else:
                        target_member_names = archive_file.names_by_filename(
                            target_name
                        )
                        if len(target_member_names) > 1:
                            raise cls.MultipleBinaryMatchesFound(
                                f"multiple binary matches were found in archive {resolved_asset.name}: {target_member_names}"
                            )
                        if len(target_member_names) == 0:
                            raise cls.MoBinaryMatchesFound(
                                f"no binary named {target_name} found in archive {resolved_asset.name}"
                            )
                        target_member_name = target_member_names[0]

                    logger.warning(
                        "target binary found in tar as member: %s", target_member_name
                    )

                    same_dir_members = archive_file.get_names_by_prefix(
                        os.path.dirname(target_member_name)
                    )

                    if len(same_dir_members) == 1:
                        # In case of a single file, copy it into bin location and rename it as the target name
                        archive_file.extract(target_member_name, temp_extraction_path)
                        if target_member_name != target_name:
                            logger.warning(
                                "renaming %s to %s", target_member_name, target_name
                            )
                        shutil.copyfile(
                            temp_extraction_path.joinpath(target_member_name),
                            final_binary_location,
                        )
                        cls._recursive_chmod(final_binary_location, cls.BIN_PERMISSIONS)

                    else:
                        # In case other files in same dir, assume lib dir.
                        # extracting to lib location and soft link the target into bin location
                        target_lib_location = lib_location.joinpath(target_name)

                        logger.warning(
                            "extracting %s into %s",
                            resolved_asset.name,
                            target_lib_location,
                        )

                        if target_lib_location.exists() and not force:
                            raise cls.TargetExists(
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
                            raise cls.TargetExists(
                                f"{target_lib_location} already exists"
                            ) from exc

                        lib_binary_location = target_lib_location.joinpath(
                            target_member_name
                        )

                        # execute permissions
                        cls._recursive_chmod(target_lib_location, cls.BIN_PERMISSIONS)

                        logger.warning(
                            "linking %s to %s",
                            lib_binary_location,
                            final_binary_location,
                        )
                        try:
                            os.symlink(lib_binary_location, final_binary_location)
                        except FileExistsError as exc:
                            os.remove(final_binary_location)
                            os.symlink(lib_binary_location, final_binary_location)

            else:
                # assumes regular binary
                shutil.copyfile(temp_asset_path, final_binary_location)
                cls._recursive_chmod(final_binary_location, cls.BIN_PERMISSIONS)

            # execute permissions
            # st = os.stat(final_binary_location)
            # os.chmod(final_binary_location, st.st_mode | stat.S_IEXEC)
