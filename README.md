# Nanolayer CLI


## Installation


`pipx install nanolayer`


### GH Release installation:
Usage:

```shell
nanolayer install gh cli/cli gh 
```

### Comparisons
Regular:

```dockerfile
FROM python:3.10

RUN apt-get -y update && apt-get install -y htop 
```

With nanolayer:

```dockerfile
FROM python:3.10

RUN curl -sfL https://github.com/devcontainers-contrib/cli/releases/download/v0.4.0rc0/nanolayer-x86_64-unknown-linux-gnu.tgz | tar fxvz - -C /tmp && \
    chmod 755 /tmp/nanolayer && ls /tmp && \
    /tmp/nanolayer install apt-get htop && \
    rm /tmp/nanolayer
```
