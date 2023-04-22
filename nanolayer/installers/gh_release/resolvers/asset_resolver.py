import json
import logging
import re
import urllib
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra

from nanolayer.utils.linux_information_desk import LinuxInformationDesk

logger = logging.getLogger(__name__)


class AssetResolver:
    ARCH_REGEX_MAP = {
        LinuxInformationDesk.Architecture.ARMV6: "([Aa][Rr][Mm]v6)",
        LinuxInformationDesk.Architecture.ARMV7: "([Aa][Rr][Mm]v7)",
        LinuxInformationDesk.Architecture.ARMHF: "([Aa][Rr][Mm]hf)",
        LinuxInformationDesk.Architecture.I386: "(i386|-386|_386)",
        LinuxInformationDesk.Architecture.ARM32: "([Aa]rm32|ARM32)",
        LinuxInformationDesk.Architecture.ARM64: "([Aa]rm64|ARM64|-ARM)",
        LinuxInformationDesk.Architecture.S390: "(s390x|s390)",
        LinuxInformationDesk.Architecture.PPC64: "(-ppc|ppc64|PPC64|_ppc)",
        LinuxInformationDesk.Architecture.x86_64: "([Aa]md64|-x64|x64|x86[_-]64)",
    }

    class PlatformType(Enum):
        WINDOWS = "WINDOWS"
        LINUX = "LINUX"
        OSX = "OSX"
        IOS = "IOS"
        ANDROID = "ANDROID"
        TVOS = "TVOS"
        ILLUMOS = "ILLUMOS"
        SOLARIS = "SOLARIS"
        FREEBSD = "FREEBSD"
        NETBSD = "NETBSD"
        WASI = "WASI"
        BROWSER = "BROWSER"
        MACCATALYST = "MACCATALYST"

    BITNESS_REGEX_MAP = {
        LinuxInformationDesk.Bitness.B32BIT: r"(32[Bb]it)",
        LinuxInformationDesk.Bitness.B64BIT: r"(64[Bb]it)",
    }

    PLATFORM_REGEX_MAP = {
        PlatformType.WINDOWS: r"(windows|Windows|WINDOWS|win32|-win-|\.msi$|.msixbundle$|\.exe$)",
        PlatformType.LINUX: r"([Ll]inux)",
        PlatformType.OSX: r"(macOS|mac-os|-osx-|_osx_|[Dd]arwin)",
        PlatformType.ILLUMOS: r"([Ii]llumos|[Oo]mni[oO][sS]|[Oo]pen[Ii]ndiana|[Tt]ribblix)",
    }

    RELEASE_ID_REGEX_MAP = {
        enum: f"(?i)({enum.value})" for enum in LinuxInformationDesk.LinuxReleaseID
    }
    RELEASE_ID_REGEX_MAP[
        LinuxInformationDesk.LinuxReleaseID.alpine
    ] = r"(?i)(alpine|musl)"  # adding musl to alpine "tells"

    MISC_REGEX_MAP = {
        "packages": r"(\.deb|\.rpm|\.pkg|\.apk)",
        "checksums": r"(\.sig$|\.text$|\.txt$|[Cc]hecksums|sha256)",
        "certificates": r"(\.pub$|\.pem$|\.crt$|\.asc$|pivkey|pkcs11key)",
        "metadata": r"(\.json$|\.sbom$)",
    }

    class AssetResolverError(Exception):
        pass

    class ReleaseAsset(BaseModel):
        class Config:
            extra = Extra.ignore

        name: str
        browser_download_url: str
        label: Optional[str] = None
        size: int

    class FindAllRegexFilter:
        def __init__(self, name: str, regex: str, negative: bool) -> None:
            self.name = name
            self.regex = regex
            self.negative = negative

        def __call__(self, asset: "AssetResolver.ReleaseAsset") -> bool:
            print(self.name)
            matches = len(re.findall(self.regex, asset.name))
            return matches > 0 if not self.negative else matches == 0

    class MatchRegexFilter:
        def __init__(self, name: str, regex: str, negative: bool) -> None:
            self.name = name
            self.regex = regex
            self.negative = negative

        def __call__(self, asset: "AssetResolver.ReleaseAsset") -> bool:
            match = re.match(self.regex, asset.name)
            return match is not None if not self.negative else match is None

    @classmethod
    def _get_release_dict(cls, repo: str, tag: str) -> Dict[str, Any]:
        response = urllib.request.urlopen(
            f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        )  # nosec
        return json.loads(response.read())

    @classmethod
    def _get_release_assets(
        cls, repo: str, release_version: str
    ) -> List["AssetResolver.ReleaseAsset"]:
        release_dict = cls._get_release_dict(repo=repo, tag=release_version)
        return [cls.ReleaseAsset.parse_obj(asset) for asset in release_dict["assets"]]

    @classmethod
    def resolve(
        cls,
        repo: str,
        release_version: str,
        binary_names: List[str],
        asset_regex: Optional[str] = None,
        arch: Optional[LinuxInformationDesk.Architecture] = None,
    ) -> "AssetResolver.ReleaseAsset":
        assert not (
            asset_regex is None and arch is None
        ), "at least one of 'asset_regex','arch' arguments must be given"

        assets = cls._get_release_assets(repo=repo, release_version=release_version)

        if asset_regex is not None:
            assets = list(
                filter(
                    cls.FindAllRegexFilter(
                        name="user asset regex", regex=asset_regex, negative=False
                    ),
                    assets,
                )
            )
            if len(assets) == 1:
                return assets[0]

            if len(assets) == 0:
                raise cls.AssetResolverError(
                    f"no matches found for asset regex: {asset_regex}"
                )

            logger.warning(
                "asset regex: %s has filtered assets down to %s candidates: %s. Proceding to builtin filters",
                asset_regex,
                len(assets),
                str([asset.name for asset in assets]),
            )

        # add all non-requested architecture as a negative filters
        bad_architecture_regexes = deepcopy(cls.ARCH_REGEX_MAP)
        bad_architecture_regexes.pop(arch)
        negative_architecture_filters = [
            cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
            for name, regex in bad_architecture_regexes.items()
        ]

        # add misc files like checksums and packages as negative filters
        negative_misc_filters = [
            cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
            for name, regex in cls.MISC_REGEX_MAP.items()
        ]

        # add all non-current platform as a negative filters
        bad_platform_regexes = deepcopy(cls.PLATFORM_REGEX_MAP)
        bad_platform_regexes.pop(cls.PlatformType.LINUX)
        negative_platform_filters = [
            cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
            for name, regex in bad_platform_regexes.items()
        ]

        # add all non-current bitness as a negative filters
        bad_bitness_regexes = deepcopy(cls.BITNESS_REGEX_MAP)
        bad_bitness_regexes.pop(LinuxInformationDesk.get_bitness())
        negative_bitness_filters = [
            cls.FindAllRegexFilter(name=name, regex=regex, negative=True)
            for name, regex in bad_bitness_regexes.items()
        ]

        # One filter to rule them all
        assets = filter(
            lambda asset: all(
                f(asset)
                for f in (
                    negative_architecture_filters
                    + negative_misc_filters
                    + negative_platform_filters
                    + negative_bitness_filters
                )
            ),
            assets,
        )

        # actually run the filters...
        assets = list(assets)

        if len(assets) == 1:
            return assets[0]

        elif len(assets) == 0:
            raise cls.AssetResolverError("No matches found")

        # positive filters are being run one by one, because we want to discard those
        # who filter out all of the remaining.

        positive_filters = [
            cls.FindAllRegexFilter(
                name=f"contains binary name: {binary_name} ",
                regex=f".*{binary_name}.*",
                negative=False,
            )
            for binary_name in binary_names
        ] + [
            cls.FindAllRegexFilter(
                name=arch.value, regex=cls.ARCH_REGEX_MAP[arch], negative=False
            ),
            cls.FindAllRegexFilter(
                name=cls.PlatformType.LINUX.value,
                regex=cls.PLATFORM_REGEX_MAP[cls.PlatformType.LINUX],
                negative=False,
            ),
            cls.FindAllRegexFilter(
                name="prefer own distro",  # prefer own exact distro
                regex=cls.RELEASE_ID_REGEX_MAP[LinuxInformationDesk.get_release_id()],
                negative=False,
            ),
            cls.FindAllRegexFilter(
                name="prefer static",  # less dynamic linking, more portability
                regex=".*static.*",
                negative=False,
            ),
            cls.FindAllRegexFilter(
                name="prefer own distro-like",  # prefer own distro like
                regex=cls.RELEASE_ID_REGEX_MAP[
                    LinuxInformationDesk.get_release_id(id_like=True)
                ],
                negative=False,
            ),
        ]

        bad_distros_regexes = {
            key: val
            for key, val in cls.RELEASE_ID_REGEX_MAP.items()
            if key
            not in (
                LinuxInformationDesk.get_release_id(),
                LinuxInformationDesk.get_release_id(id_like=True),
            )
        }
        for bad_distro_id, bad_distro_regex in bad_distros_regexes.items():
            positive_filters.append(
                cls.FindAllRegexFilter(
                    name=f"prefer non {bad_distro_id}",  # prefer own distro like
                    regex=bad_distro_regex,
                    negative=True,
                )
            )

        for positive_filter in positive_filters:
            filtered_assets = list(filter(positive_filter, assets))

            if len(filtered_assets) == 0:
                # filter is too aggressive. ignoring it
                continue
            else:
                assets = filtered_assets

        if len(assets) > 1:
            raise cls.AssetResolverError(
                f"Too many matches found: {str([asset.name for asset in assets])}"
            )

        return assets[0]
