#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 


ensure_sudo () {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e 'Must be run as root. Use sudo, su, or add "USER root" to your Dockerfile before running this script.'
        exit 1
    fi
}

