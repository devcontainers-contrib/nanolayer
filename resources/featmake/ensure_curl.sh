#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 


ensure_curl () {
    if ! type curl >/dev/null 2>&1; then
        echo "curl not found, installing..."
        apt-get update -y && apt-get -y install --no-install-recommends curl
    fi 
}
