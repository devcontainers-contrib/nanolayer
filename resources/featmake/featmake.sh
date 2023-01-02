#!/bin/bash -l
# This is part of the devconainer-contrib cli 
# For more information: https://github.com/devcontainers-contrib/cli 

source ./clean_up

source ./ensure_sudo

source ./ensure_curl

source ./ensure_oras

source ./set_envs

source ./set_remote_user

set -e

FEATURE_OCI=$1

trap clean_up EXIT

ensure_sudo
set_remote_user
ensure_curl
ensure_oras

temp_dir=$(mktemp -d)
oras pull "$FEATURE_OCI" --output $temp_dir/
tar -xf $temp_dir/*.tgz -C $temp_dir/
( cd $temp_dir ; set_envs "devcontainer-feature.json" ;  source ./install.sh )
rm -rf $temp_dir
