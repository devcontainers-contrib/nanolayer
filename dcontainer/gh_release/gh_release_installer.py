import logging
import shutil
from typing import List, Optional, Dict, Any, Union
import uuid
import invoke
from dcontainer.utils.invoker import Invoker
import re
import os
import semver
import stat
from fsspec.implementations.tar import TarFileSystem
import urllib
from pathlib import Path
import json
from pydantic import BaseModel, Extra
import tempfile
import tarfile
import zipfile

from dcontainer.utils.linux_information_desk import LinuxInformationDesk

logger= logging.getLogger(__name__)
from tarfile import TarFile


class ExtendedTarFile(TarFile):

    def extract_prefix(self, prefix: str) -> None:
        subdir_and_files = [
            tarinfo for tarinfo in self.getmembers()
            if tarinfo.name.startswith(prefix)
        ]
        self.extractall(members=subdir_and_files)


    def get_names_by_prefix(self, prefix: str) -> None:
        subdir_and_files = [
            name for name in self.getnames()
            if name.startswith(prefix)
        ]
        return subdir_and_files

    def get_names_by_suffix(self, suffix: str) -> None:
        subdir_and_files = [
            name for name in self.getnames()
            if name.endswith(suffix)
        ]
        return subdir_and_files

    def names_by_filename(self, filename: str) -> List[str]:
        matching_members = self.get_names_by_suffix(suffix=f"/{filename}")
        # could also be as root member
        if filename in self.getnames():
            matching_members.append(filename)

        return matching_members
       


class GHReleaseInstaller:
    X86_X64_REGEX = ""
    ARM_REGEX = ""
    X64_APPLE_REGEX = ""
    ARM_APPLE_REGEX = ""
    

    BIN_PERMISSIONS = "755"
    class ReleaseAsset(BaseModel):
        class Config:
            extra = Extra.ignore
        
        name: str
        browser_download_url: str
        label: Optional[str] = None
        size: int

    GIT_VERSION_TAG_REGEX = "(?:tags\/)(v)?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+)?$"


    class NoAssetsFound(Exception):
        pass

    class NoPremissions(PermissionError):
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
        response = invoke.run(f"git ls-remote --tags https://github.com/{repo}", pty=True, hide=True)
        if response.ok:
            matches = [ re.findall(cls.GIT_VERSION_TAG_REGEX, line.strip()) for line in response.stdout.split('\n')]
        return [ match[0][0] + ".".join(match[0][1:-1]) + match[0][-1]  for match in matches if len(match) == 1]
    
    @classmethod
    def get_latest_stable_version(cls, repo: str) -> List[str]:
        all_version_tags = cls.get_version_tags(repo)

        def strip_prefix(value:str, prefix: str) -> str:
            if value[:len(prefix)] == prefix:
                return value[len(prefix):]
            return value
            
        semversions = [semver.VersionInfo.parse(strip_prefix(version, "v")) if semver.VersionInfo.isvalid(strip_prefix(version, "v")) else semver.VersionInfo(0,0,0) for version in all_version_tags ]

        sorted_tuples = sorted(zip(semversions, all_version_tags), key=lambda pair: pair[0])


        stable_semversions = list(filter(lambda version_tuple : version_tuple[0].build is None and version_tuple[0].prerelease is None, sorted_tuples))

        return str(stable_semversions[-1][1])
    
    @classmethod
    def _get_release_by_tag(cls, repo: str, tag: str) -> Dict[str, Any]:
        response = urllib.request.urlopen(
                f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
            )  # nosec
        return json.loads(response.read())
    

    @classmethod
    def _get_assets_by_tag(cls, repo: str, tag: str) -> List['GHReleaseInstaller.ReleaseAsset']:
        release_dict = cls._get_release_by_tag(repo=repo, tag=tag)
        return [cls.ReleaseAsset.parse_obj(asset) for asset in release_dict['assets']]
    
    @classmethod
    def get_asset(cls, url: str, headers: Optional[Dict[str,str]] = None) -> bytes:

        if not url.startswith("http"):
            raise ValueError("only http/https links are permited")

        if headers is None:
            headers = {}

        if "User-Agent" not in headers:
            headers["User-Agent"] = "dcontainer"

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
                raise cls.ReleaseVersionNotFound(f"Could not find a release version: {asked_version}")
    
    
    @classmethod
    def resolve_asset(cls, repo: str, tag: str, asset_regex: Optional[str] = None) -> "GHReleaseInstaller.ReleaseAsset":
        assets = cls._get_assets_by_tag(repo=repo, tag=tag)
        if asset_regex is not None:
            assets = list(filter(lambda asset: re.match(asset_regex, asset.name) is not None, assets))
            if len(assets) == 0:
                raise cls.NoAssetsFound(f"no matches found for asset regex: {asset_regex}")
            elif len(assets) >= 2:
                raise cls.NoAssetsFound(f"More than one match was found for asset regex: {asset_regex}\n {assets}\n Please narrow down the asset regex")
            else:
                return assets[0]
        else:
            raise NotImplementedError()

    @classmethod
    def resolve_bin_location(cls) -> str:
        # todo: return based on linux distro
        return "/usr/local/bin"
    
    
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
        arch: Optional[str]  = None,
        platform: Optional[str]  = None,
        checksum_regex: Optional[str] = None,
        checksum: Optional[bool] = True,
    ) -> None:
        
        if not LinuxInformationDesk.has_root_privileges():
            raise cls.NoPremissions("please run as root or with sudo")

        if bin_location is None:
            bin_location = cls.resolve_bin_location()

        if isinstance(bin_location, str):
            bin_location = Path(bin_location)
        assert bin_location.is_dir()


        if lib_location is None:
            lib_location = cls.resolve_lib_location()
        if isinstance(lib_location, str):
            lib_location = Path(lib_location)
        assert lib_location.is_dir()

        
        final_binary_location = bin_location.joinpath(target_name)

        if final_binary_location.exists() and not force:
            raise cls.TargetExists(f"target {final_binary_location} already exists")
        
        # Will raise an exception if release for the requested version does not exists
        version = cls.resolve_release_version(asked_version=version, repo=repo)
        
        # will raise an exception if more or less than a single asset can meet the requirments
        resolved_asset = cls.resolve_asset(repo=repo, tag=version, asset_regex=asset_regex)

        # 
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            temp_asset_path = tempdir.joinpath("temp_asset")
            temp_extraction_path = tempdir.joinpath("temp_extraction")
            cls.download_asset(url=resolved_asset.browser_download_url, target=temp_asset_path)
            
            if tarfile.is_tarfile(temp_asset_path):

                with ExtendedTarFile.open(temp_asset_path) as tarf:

                    # resolve target member name 
                    if len(tarf.getnames()) == 1:
                        # In case of a single member, use it no matter how its named
                        target_member_name = tarf.getnames()[0]
                    else:
                        target_member_names = tarf.names_by_filename(target_name)
                        if len(target_member_names) > 1:
                            raise cls.MultipleBinaryMatchesFound(f"multiple binary matches were found in archive {resolved_asset.name}: {target_members}")
                        if len(target_member_names) == 0:
                            raise cls.MoBinaryMatchesFound(f"no binary named {target_name} found in archive {resolved_asset.name}")
                        target_member_name = target_member_names[0]


                    same_dir_members = tarf.get_names_by_prefix(os.path.dirname(target_member_name))
                    if len(same_dir_members) == 1:
                        tarf.extract(target_member_name, temp_extraction_path)
                        if target_member_name != target_name:
                            logger.warning("renaming %s to %s", target_member_name, target_name)
                        shutil.copyfile(temp_extraction_path.joinpath(target_member_name), final_binary_location)
                        cls._recursive_chmod(final_binary_location, cls.BIN_PERMISSIONS)

                    else:
                        # In case other files in same dir, assume lib dir. 
                        # extracting to lib location and soft link the target into bin location
                        logger.warning("extracting %s into %s", resolved_asset.name, lib_location)
                        target_lib_location = lib_location.joinpath(target_name)

                        if target_lib_location.exists() and not force:
                            raise cls.TargetExists(f"{target_lib_location} already exists")

                        tarf.extractall(temp_extraction_path)
                        
                        try:
                            shutil.copytree(temp_extraction_path, target_lib_location, dirs_exist_ok=force)
                        except FileExistsError as exc:
                            raise cls.TargetExists(f"{target_lib_location} already exists") from exc
                        
                        lib_binary_location = target_lib_location.joinpath(target_name)
                        
                        # execute permissions
                        cls._recursive_chmod(target_lib_location, cls.BIN_PERMISSIONS)

                        logger.warning("linking %s to %s", lib_binary_location, final_binary_location)
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
                        
            
        