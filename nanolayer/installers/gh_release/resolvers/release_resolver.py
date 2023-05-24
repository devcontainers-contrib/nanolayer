import re
from typing import Any, Dict, List

import invoke
from natsort import natsorted


class ReleaseResolver:
    class ReleaseResolverError(Exception):
        pass

    GIT_VERSION_TAG_REGEX = "(?:tags\/)(v?[0-9]+\.[0-9]+\.?[0-9]+?)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+)?$"

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
            # merge match tuples into a full version string
            stringified_matches = [
                "".join(match[0]) for match in matches if len(match) == 1
            ]
            return stringified_matches
        return []

    @classmethod
    def get_latest_stable_version(cls, repo: str) -> List[str]:
        all_version_tags = cls.get_version_tags(repo)

        return natsorted(all_version_tags)[-1]

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
