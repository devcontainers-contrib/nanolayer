#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 

set -e

FEATURE_OCI=$1

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
    # Sets up the default values the devcontainer-feature.json has declared for each option
    # This is part of the devconainer-contrib cli 
    # For more information: https://github.com/devcontainers-contrib/cli 

    FILE_NAME=$1
    OPTION_NAMES=($(cat $FILE_NAME | jq -cr '.options | keys[]' |  awk '{ print toupper($0) }'))
    
    # we do this in order to account for empty string values
    OPTION_DEFAULT_VALUES=()
    while read -r line; do 
        OPTION_DEFAULT_VALUES+=("$line") 
    done <<< "$(cat $FILE_NAME | jq -cr '.options[].default')"

    arraylength="${#OPTION_NAMES[@]}"

    for (( i=0; i<${arraylength}; i++ )); do
        current_option=${OPTION_NAMES[i]}
        current_default_value=${DEFAULT_VALUES[i]}

        # setting defaults only if not explicitely given
        if [ -z "${!current_option}" ] ; then
            export $current_option=$current_default_value
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

set_remote_user
ensure_curl
ensure_oras

temp_dir=$(mktemp -d)
oras pull "$FEATURE_OCI" --output $temp_dir/
tar -xf $temp_dir/*.tgz -C $temp_dir/
( cd $temp_dir ; set_envs "devcontainer-feature.json" ;  source ./install.sh )
rm -rf $temp_dir
