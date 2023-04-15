import json
import re
import urllib
from typing import Any, Dict, List

import invoke
import semver


class ReleaseResolver:
    class ReleaseResolverError(Exception):
        pass

    GIT_VERSION_TAG_REGEX = "(?:tags\/)(v)?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+)?$"

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
    def resolve(cls, asked_version: str, repo: str) -> Dict[str, Any]:
        if asked_version == "latest":
            tag = cls.get_latest_stable_version(repo)
        else:
            versions = cls.get_version_tags(repo)
            if asked_version in versions:
                tag = asked_version

            elif f"v{asked_version}" in versions:
                tag = f"v{asked_version}"

            else:
                raise cls.ReleaseResolverError(
                    f"Could not find a release for asked version: {asked_version}"
                )
        return tag
