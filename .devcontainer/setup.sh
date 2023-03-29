#!/usr/bin/env bash

npm install -g @devcontainers/cli


pip install -e .[dev,generate]

apt-get install qemu binfmt-support qemu-user-static
