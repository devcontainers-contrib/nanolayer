from easyfs import File
from devcontainer_contrib.models.devcontainer_feature_definition import (
    FeatureDefinition,
)


class DevcontainerFeatureJson(File):
    def __init__(self, definition_model: FeatureDefinition) -> None:

        super().__init__(
            definition_model.to_feature_model()
            .json(indent=4, exclude_none=True)
            .encode()
        )
