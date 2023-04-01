# Nanolayer CLI

`nanolayer` helps keep container layers as small as possible.

It does so by automatically deleting any installation leftovers (such as apt-get update lists, ppas, etc)


## Installation


`pipx install nanolayer`


### GH Release installation:
Usage:

```shell
nanolayer install gh cli/cli gh 
```

### Example 

```dockerfile
FROM python:3.10

RUN apt-get -y update && apt-get install -y htop 
```

layer size:  **22MB**

```dockerfile
FROM python:3.10

RUN curl -sfL https://github.com/devcontainers-contrib/nanolayer/releases/download/v0.4.0/nanolayer-x86_64-unknown-linux-gnu.tgz | tar fxvz - -C / && \
    chmod 755 /tmp/nanolayer && ls /tmp && \
    /nanolayer install apt-get htop && \
    rm /nanolayer
```

Layer size: **1.6MB**
