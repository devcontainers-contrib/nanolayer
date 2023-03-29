from typing import Optional
from easyfs import File

from minilayer.settings import ENV_CLI_LOCATION, ENV_FORCE_CLI_INSTALLATION
from minilayer.utils.version import resolve_own_release_version

RELEASE_LINK = """{RELEASE_VERSION}"""

HEADER = """#!/bin/bash -i


clean_download() {{
    # The purpose of this function is to download a file with minimal impact on contaier layer size
    # this means if no valid downloader is found (curl or wget) then we install a downloader (currently wget) in a 
    # temporary manner, and making sure to 
    # 1. uninstall the downloader at the return of the function
    # 2. revert back any changes to the package installer database/cache (for example apt-get lists)
    # The above steps will minimize the leftovers being created while installing the downloader 
    # Supported distros:
    #  debian/ubuntu/alpine
    
    url=$1
    output_location=$2
    tempdir=$(mktemp -d)
    downloader_installed=""

    function _apt_get_install() {{
        tempdir=$1

        # copy current state of apt list - in order to revert back later (minimize contianer layer size) 
        cp -p -R /var/lib/apt/lists $tempdir 
        apt-get update -y
        apt-get -y install --no-install-recommends wget
    }}

    function _apt_get_cleanup() {{
        tempdir=$1

        echo "removing wget"
        apt-get -y purge wget --auto-remove

        echo "revert back apt lists"
        rm -rf /var/lib/apt/lists/*
        mv -v $tempdir/lists/* /var/lib/apt/lists  
    }}

    function _apk_install() {{
        tempdir=$1
        # copy current state of apk cache - in order to revert back later (minimize contianer layer size) 
        cp -p -R /var/cache/apk $tempdir 

        apk add --no-cache  wget
    }}

    function _apk_cleanup() {{
        tempdir=$1

        echo "removing wget"
        apk del wget 
    }}
    # try to use either wget or curl if one of them already installer
    if type curl >/dev/null 2>&1; then
        downloader=curl
    elif type wget >/dev/null 2>&1; then
        downloader=wget
    else
        downloader=""
    fi

    # in case none of them is installed, install wget temporarly
    if [ -z $downloader ] ; then
        if [ -x "/usr/bin/apt-get" ] ; then
            _apt_get_install $tempdir
        elif [ -x "/sbin/apk" ] ; then
            _apk_install $tempdir
        else
            echo "distro not supported"
            exit 1
        fi
        downloader="wget"
        downloader_installed="true"
    fi

    if [ $downloader = "wget" ] ; then
        wget -q $url -O $output_location
    else
        curl -sfL $url -o $output_location 
    fi

    # NOTE: the cleanup procedure was not implemented using `trap X RETURN` only because
    # alpine lack bash, and RETURN is not a valid signal under sh shell
    if ! [ -z $downloader_installed  ] ; then
        if [ -x "/usr/bin/apt-get" ] ; then
            _apt_get_cleanup $tempdir
        elif [ -x "/sbin/apk" ] ; then
            _apk_cleanup $tempdir
        else
            echo "distro not supported"
            exit 1
        fi
    fi 

}}


ensure_dcontainer() {{
    # Ensure existance of the dcontainer cli program
    local variable_name=$1
    local dcontainer_location=""

    # If possible - try to use an already installed dcontainer
    if [[ -z "${{{force_cli_installation_env}}}" ]]; then
        if [[ -z "${{{cli_location_env}}}" ]]; then
            if type dcontainer >/dev/null 2>&1; then
                echo "Using a pre-existing dcontainer"
                dcontainer_location=dcontainer
            fi
        elif [ -f "${{{cli_location_env}}}" ] && [ -x "${{{cli_location_env}}}" ] ; then
            echo "Using a pre-existing dcontainer which were given in env varialbe"
            dcontainer_location=${{{cli_location_env}}}
        fi
    fi

    # If not previuse installation found, download it temporarly and delete at the end of the script 
    if [[ -z "${{dcontainer_location}}" ]]; then

        if [ "$(uname -sm)" == "Linux x86_64" ] || [ "$(uname -sm)" == "Linux aarch64" ]; then
            tmp_dir=$(mktemp -d -t dcontainer-XXXXXXXXXX)

            clean_up () {{
                ARG=$?
                rm -rf $tmp_dir
                exit $ARG
            }}
            trap clean_up EXIT

            tar_filename=dcontainer-"$(uname -m)"-unknown-linux-gnu.tgz

            # clean download will minimize leftover in case a downloaderlike wget or curl need to be installed
            clean_download https://github.com/devcontainers-contrib/cli/releases/download/{release_version}/$tar_filename $tmp_dir/$tar_filename
            
            tar xfzv $tmp_dir/$tar_filename -C "$tmp_dir"
            chmod a+x $tmp_dir/dcontainer
            dcontainer_location=$tmp_dir/dcontainer
        else
            echo "No binaries compiled for non-x86-linux architectures yet: $(uname -m)"
            exit 1
        fi
    fi

    # Expose outside the resolved location
    declare -g ${{variable_name}}=$dcontainer_location

}}


"""


class LibraryScriptsSH(File):
    def __init__(
        self,
        release_version: Optional[str] = None,
    ) -> None:
        self.release_version = release_version
        super().__init__(self.to_str().encode())

    def to_str(self):
        try:
            release_version = self.release_version or resolve_own_release_version()
        except Exception as e:
            raise ValueError(
                "could not resolve release version because of error, please manually set release_verison"
            ) from e

        return HEADER.format(
            release_version=release_version,
            force_cli_installation_env=ENV_FORCE_CLI_INSTALLATION,
            cli_location_env=ENV_CLI_LOCATION,
        )
