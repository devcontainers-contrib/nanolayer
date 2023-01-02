#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 


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
