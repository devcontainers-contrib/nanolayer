#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 


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