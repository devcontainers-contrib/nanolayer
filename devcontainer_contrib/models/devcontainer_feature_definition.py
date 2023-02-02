from __future__ import annotations

from unittest import mock
from typing import Any, Dict, List, Optional, Union
from devcontainer_contrib.models.devcontainer_feature import Feature
from pydantic import BaseModel, Extra, Field


class FeatureDependency(BaseModel):
    feature: str
    options: Dict[str, Union[str, bool]]


class TestScenario(BaseModel):
    name: str
    image: str
    test_commands: List[str]
    options: Dict[str, Union[str, bool]]


class FeatureDependencies(BaseModel):
    __root__: List[FeatureDependency]

    def __iter__(self):
        return iter(self.__root__)

    def __len__(self):
        return len(self.__root__)

    def __getattr__(self, k):
        return getattr(self.__root__, k)


class FeatureDefinition(Feature):
    class Config:
        extra = Extra.forbid

    dependencies: Optional[FeatureDependencies] = Field(
        None,
        description="Possible user-configurable feature dependencies for this Feature. The selected features and their params will be installed prior to running the installation command",
    )

    install_command: Optional[str] = Field(
        None,
        description="This command will be run after dependencies are all installed",
    )

    test_scenarios: List[TestScenario] = Field(
        None,
        description="List of test scenarios to prepare testing different use cases",
    )

    def to_feature_model(self) -> Feature:
        with mock.patch.object(Feature.Config, "extra", Extra.ignore):
            return Feature(**self.dict())
