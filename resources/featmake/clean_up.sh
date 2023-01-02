#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 




clean_up () {
    ARG=$?
    rm -rf oras_0.16.0_*.tar.gz oras-install/
    rm -rf feature-install/
    exit $ARG
} 