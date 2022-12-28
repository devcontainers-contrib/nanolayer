# Devcontainers Contrib CLI


## Installation


`pip install devcontainer-contrib`


### Feature Generation:

```
Usage: python -m devcontainer_contrib features generate [OPTIONS]
                                                        FEATURE_DEFINITION
                                                        OUTPUT_DIR

Arguments:
  FEATURE_DEFINITION  [required]
  OUTPUT_DIR          [required]

Options:
  --output-type [feature_dir|dependencies|test]
                                  [default: OutputType.feature_dir]
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

    # this command will be executed after the dependency feature list has been installed
    "install_command": "echo 'Done'",

    # this command will serve as the default test command (should exit wth code `0` if your feature is installed correctly)
    "test_command": "act --version"
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
It assumes you have the devcontainer-contrib cli already installed

```sh
git clone https://github.com/devcontainers-contrib/cli --depth 1
cd cli


devcontainer-contrib features generate "./test/resources/test_feature_definitions/elixir-asdf/feature-definition.json" "./output_dir" --output-type=feature_dir
```
