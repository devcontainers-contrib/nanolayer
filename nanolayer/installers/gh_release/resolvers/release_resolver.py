import json
import re
import urllib
from typing import Any, Dict, List, Optional

import invoke
from natsort import natsorted


class ReleaseResolver:
    class ReleaseResolverError(Exception):
        pass

    GIT_VERSION_TAG_REGEX = r"(?:tags\/)([0-9A-Za-z\-\_|.]+)\\?$"

    @classmethod
    def _filter_tags_by_regex(cls, tags: List[str], regex: str) -> List[str]:
        return list(
            filter(
                lambda match: re.match(regex, match) is not None,
                tags,
            )
        )

    @classmethod
    def get_version_tags(
        cls, repo: str, release_tag_regex: Optional[str] = None
    ) -> List[str]:
        response = invoke.run(
            f"git ls-remote --tags https://github.com/{repo}", pty=True, hide=True
        )
        if response.ok:
            matches = [
                re.findall(cls.GIT_VERSION_TAG_REGEX, line.strip())
                for line in response.stdout.split("\n")
            ]
            # merge match tuples into a full version string
            stringified_matches = [match[0] for match in matches if len(match) == 1]

            if release_tag_regex is not None:
                stringified_matches = cls._filter_tags_by_regex(
                    stringified_matches, release_tag_regex
                )
            return stringified_matches
        return []

    @classmethod
    def get_latest_git_version_tag(
        cls, repo: str, release_tag_regex: Optional[str] = None
    ) -> str:
        all_version_tags = cls.get_version_tags(repo, release_tag_regex)

        return natsorted(all_version_tags)[-1]

    @classmethod
    def get_latest_release_tag(
        cls, repo: str, release_tag_regex: Optional[str] = None
    ) -> str:
        response = urllib.request.urlopen(
            f"https://api.github.com/repos/{repo}/releases"
        )  # nosec
        release_dicts = json.loads(response.read())
        release_tags = [release_dict["tag_name"] for release_dict in release_dicts]
        if release_tag_regex is not None:
            release_tags = cls._filter_tags_by_regex(release_tags, release_tag_regex)
        return natsorted(release_tags)[-1]

    @classmethod
    def resolve(
        cls,
        asked_version: str,
        repo: str,
        release_tag_regex: Optional[str] = None,
        use_github_api: bool = False,
    ) -> str:
        if asked_version == "latest":
            if use_github_api:
                return cls.get_latest_release_tag(repo, release_tag_regex)
            return cls.get_latest_git_version_tag(repo, release_tag_regex)

        else:
            versions = cls.get_version_tags(repo, release_tag_regex)
            if asked_version in versions:
                tag = asked_version

            elif f"v{asked_version}" in versions:
                tag = f"v{asked_version}"

            else:
                raise cls.ReleaseResolverError(
                    f"Could not find a release for asked version: {asked_version}"
                )
        return tag
