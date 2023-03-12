# Dcontainer CLI


## Installation


`pip install dcontainer[generate]`


### Feature Generation:

```
Usage: python -m dcontainer feature generate [OPTIONS]
                                                        FEATURE_DEFINITION
                                                        OUTPUT_DIR

Arguments:
  FEATURE_DEFINITION  [required]
  OUTPUT_DIR          [required]

Options:
  --help                          Show this message and exit.
```


Input for feature generation is a `feature-definition.json` file
This is an *extended* version of the [devcontainer-feature.json](https://containers.dev/implementors/features/#devcontainer-feature-json-properties) file with *additional fields*:

```yaml
{   
    ...
    regular devcontainer-json fields  like id, name, description etc
    ...


    # dependencies are list of features and options  (those will be installed as prerequisites to your feature)
    "dependencies": [
        {
            "feature": "ghcr.io/devcontainers-contrib/features/asdf-package:latest",
            "options": {
                "plugin": "act",

                "version": "latest"
            }
        }
    ],

    # This command will be executed after the dependency feature list has been installed
    "install_command": "echo 'Done'",

    # this example test scenario checks the default options (empty options dict), each test_command should exit wth code `0` if your feature is installed correctly.
    "test_scenarios": [
        {
            "name": "test_defaults",
            "image": "mcr.microsoft.com/devcontainers/base:debian",
            "test_commands": [
                "act --version"
            ],
            "options": {}
        }
    ]
}
```

#### redirect input

```yaml
{
    ...


    "options": {
        "version": {
            "type": "string",
            "default": "latest",
            "description": "Select the version of act to install."
        }
    },

    # you can also redirect one of your actual devcontainer-feature.json options values into a dependency input, note the `$options.version` pointer to the asdf-package version option
    "dependencies": [
        {
            "feature": "ghcr.io/devcontainers-contrib/features/asdf-package:latest",
            "options": {
                "plugin": "act",
                "version": "$options.version"
            }
        }
    ],

    ...
}
```

### Usage example


this will generate the Elixir feature 
It assumes you have the dcontainer cli already installed

```sh
git clone https://github.com/devcontainers-contrib/cli --depth 1
cd cli


dcontainer feature generate "./test/resources/test_feature_definitions/elixir-asdf/feature-definition.json" "./output_dir"
```
