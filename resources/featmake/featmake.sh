#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 

set -e

_featmake_feature_oci=$1
_featmake_all_arguments=("$@")
_featmake_env_arguments=("${_featmake_all_arguments[@]:1}")

if [ "$(id -u)" -ne 0 ]; then
	echo -e 'Must be run as root. Use sudo, su, or add "USER root" to your Dockerfile before running this script.'
	exit 1
fi

clean_up () {
    ARG=$?
    rm -rf oras_0.16.0_*.tar.gz oras-install/
    rm -rf feature-install/
    exit $ARG
} 
trap clean_up EXIT

ensure_alpine_compatible() {
    . /etc/os-release
    if [ "${ID}" = "alpine" ]; then
        apk add --no-cache bash libc6-compat
    fi
}

ensure_oras () {
    # Install oras if does not exists
    # This is part of the devconainer-contrib cli 
    # For more information: https://github.com/devcontainers-contrib/cli 

    if ! type oras >/dev/null 2>&1; then
        echo "oras not found, installing..."
        curl -LO https://github.com/oras-project/oras/releases/download/v0.16.0/oras_0.16.0_linux_amd64.tar.gz
        mkdir -p oras-install/
        tar -zxf oras_0.16.0_*.tar.gz -C oras-install/
        mv oras-install/oras /usr/local/bin/
        rm -rf oras_0.16.0_*.tar.gz oras-install/
    fi 
}


ensure_curl () {
    if ! type curl >/dev/null 2>&1; then
        echo "curl not found, installing..."
        apt-get update -y && apt-get -y install --no-install-recommends curl
    fi 
}


set_envs () {
    # Sets up the argument given as env variables
    # for example 
    #    -hello world -SOME message 
    # is being parsed as 
    #     hello=world  SOME=message
    # For args which are not given, it sets up the default values the 
    # devcontainer-feature.json has declared for each option

    # This is part of the devconainer-contrib cli 
    # For more information: https://github.com/devcontainers-contrib/cli 
    FILE_NAME=$1
    shift;

    if ! [ $(($# % 2)) -eq 0 ];
    then
        echo "Bad argument number" && exit 1; 
    fi

    options_by_arguments=()
    until [ $# -eq 0 ]
    do
        if ! [[  $1 == -* ]] ; then 
            echo "Bad argument: '$1'" && exit 1; 
        fi

        name=${1:1}; shift;

        if [[ $1 == -* ]] ; then 
            echo "Bad arguments: '$name' '$1'" && exit 1; 
        else 
            export "$name"="$1"
            echo "setting $name to $1"
            options_by_arguments+=("$name")
            shift; 
        fi  
    done
    # we do this in order to account for empty string values
    OPTION_DEFAULT_VALUES=()
    while read -r line; do 
        OPTION_DEFAULT_VALUES+=("$line") 
    done <<< "$(cat $FILE_NAME | jq -cr '.options[].default')"

    OPTION_NAMES=($(cat $FILE_NAME | jq -cr '.options | keys[]' |  awk '{ print toupper($0) }'))
    arraylength="${#OPTION_NAMES[@]}"
    for (( i=0; i<${arraylength}; i++ )); do
        current_option=${OPTION_NAMES[i]}
        current_default_value=${DEFAULT_VALUES[i]}
        if [[ ! ${options_by_arguments[*]} =~ ${current_option} ]]; then
            # setting defaults only if not explicitely given
            export $current_option=$current_default_value
            echo "$current_option was not explicitely given, setting to $current_default_value"
        fi
    done
} 


set_remote_user () {
    # if _REMOTE_USER or _REMOTE_USER_HOME were not given, try to resolve them using common usernames
    # This is part of the devconainer-contrib cli 
    # For more information: https://github.com/devcontainers-contrib/cli 

    if [ "${_REMOTE_USER}" = ""  ] 
        then
        _REMOTE_USER=""
        POSSIBLE_USERS=("vscode" "node" "codespace" "$(awk -v val=1000 -F ":" '$3==val{print $1}' /etc/passwd)")
        for CURRENT_USER in "${POSSIBLE_USERS[@]}"; do
            if id -u ${CURRENT_USER} >/dev/null 2>&1; then
                _REMOTE_USER=${CURRENT_USER}
                break
            fi
        done
        if [ "${_REMOTE_USER}" = "" ]; then
            _REMOTE_USER=root
        fi
    fi
    if [ "${_REMOTE_USER_HOME}" = ""  ] 
    then
        _REMOTE_USER_HOME=$( getent passwd "$_REMOTE_USER" | cut -d: -f6 )
    fi

    echo "resolved remote username: $_REMOTE_USER , with home dir: $_REMOTE_USER_HOME"
}


ensure_alpine_compatible
set_remote_user
ensure_curl
ensure_oras

temp_dir=$(mktemp -d)
oras pull "$_featmake_feature_oci" --output $temp_dir/
tar -xf $temp_dir/*.tgz -C $temp_dir/
( cd $temp_dir ; set_envs "devcontainer-feature.json" "${_featmake_env_arguments[@]}"  ;  source ./install.sh )
rm -rf $temp_dir
