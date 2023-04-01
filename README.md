# Nanolayer CLI


## Installation


`pipx install nanolayer`


### GH Release installation:
Usage:

```shell
nanolayer install gh cli/cli gh 
```

### Comparisons

#### Nano layer

```dockerfile
FROM python:3.10

RUN curl -sfL https://github.com/devcontainers-contrib/cli/releases/download/v0.4.0/nanolayer-x86_64-unknown-linux-gnu.tgz | tar fxvz - -C / && \
    chmod 755 /tmp/nanolayer && ls /tmp && \
    /nanolayer install apt-get htop && \
    rm /nanolayer
```

layer size: 1.6MB

#### Regular layer

```dockerfile
FROM python:3.10

RUN apt-get -y update && apt-get install -y htop 
```

layer size:  22MB
