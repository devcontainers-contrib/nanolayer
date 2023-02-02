from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Extra, Field


class FeatureOptionItem(BaseModel):
    class Config:
        extra = Extra.forbid

    default: bool = Field(
        ...,
        description="Default value if the user omits this option from their configuration.",
    )
    description: Optional[str] = Field(
        None,
        description="A description of the option displayed to the user by a supporting tool.",
    )
    type: str = Field(
        ...,
        description="The type of the option. Can be 'boolean' or 'string'.  Options of type 'string' should use the 'enum' or 'proposals' property to provide a list of allowed values.",
    )


class FeatureOptionItem1(BaseModel):
    class Config:
        extra = Extra.forbid

    default: str = Field(
        ...,
        description="Default value if the user omits this option from their configuration.",
    )
    description: Optional[str] = Field(
        None,
        description="A description of the option displayed to the user by a supporting tool.",
    )
    enum: List[str] = Field(
        ...,
        description="Allowed values for this option.  Unlike 'proposals', the user cannot provide a custom value not included in the 'enum' array.",
    )
    type: str = Field(
        ...,
        description="The type of the option. Can be 'boolean' or 'string'.  Options of type 'string' should use the 'enum' or 'proposals' property to provide a list of allowed values.",
    )


class FeatureOptionItem2(BaseModel):
    class Config:
        extra = Extra.forbid

    default: str = Field(
        ...,
        description="Default value if the user omits this option from their configuration.",
    )
    description: Optional[str] = Field(
        None,
        description="A description of the option displayed to the user by a supporting tool.",
    )
    proposals: List[str] = Field(
        ...,
        description="Suggested values for this option.  Unlike 'enum', the 'proposals' attribute indicates the installation script can handle arbitrary values provided by the user.",
    )
    type: str = Field(
        ...,
        description="The type of the option. Can be 'boolean' or 'string'.  Options of type 'string' should use the 'enum' or 'proposals' property to provide a list of allowed values.",
    )


class FeatureOption(BaseModel):
    __root__: Union[FeatureOptionItem, FeatureOptionItem1, FeatureOptionItem2]


class Type(Enum):
    bind = "bind"
    volume = "volume"


class Mount(BaseModel):
    class Config:
        extra = Extra.forbid

    source: str = Field(..., description="Mount source.")
    target: str = Field(..., description="Mount target.")
    type: Type = Field(..., description="Type of mount. Can be 'bind' or 'volume'.")


class Feature(BaseModel):
    class Config:
        extra = Extra.forbid

    id: str = Field(
        ...,
        description="ID of the Feature. The id should be unique in the context of the repository/published package where the feature exists and must match the name of the directory where the devcontainer-feature.json resides.",
    )
    version: str = Field(
        ...,
        description="The version of the Feature. Follows the semanatic versioning (semver) specification.",
    )
    name: Optional[str] = Field(None, description="Display name of the Feature.")
    documentationURL: Optional[str] = Field(
        None, description="URL to documentation for the Feature."
    )

    description: Optional[str] = Field(
        None,
        description="Description of the Feature. For the best appearance in an implementing tool, refrain from including markdown or HTML in the description.",
    )
    options: Optional[Dict[str, FeatureOption]] = Field(
        None,
        description="Possible user-configurable options for this Feature. The selected options will be passed as environment variables when installing the Feature into the container.",
    )
    customizations: Optional[Dict[str, Any]] = Field(
        None,
        description="Tool-specific configuration. Each tool should use a JSON object subproperty with a unique name to group its customizations.",
    )
    installsAfter: Optional[List[str]] = Field(
        None,
        description="Array of ID's of Features that should execute before this one. Allows control for feature authors on soft dependencies between different Features.",
    )
    capAdd: Optional[List[str]] = Field(
        None,
        description="Passes docker capabilities to include when creating the dev container.",
        examples=["SYS_PTRACE"],
    )
    containerEnv: Optional[Dict[str, str]] = Field(
        None, description="Container environment variables."
    )

    entrypoint: Optional[str] = Field(
        None, description="Entrypoint script that should fire at container start up."
    )

    init: Optional[bool] = Field(
        None,
        description="Adds the tiny init process to the container (--init) when the Feature is used.",
    )

    licenseURL: Optional[str] = Field(
        None, description="URL to the license for the Feature."
    )
    mounts: Optional[List[Mount]] = Field(
        None, description="Mounts a volume or bind mount into the container."
    )

    privileged: Optional[bool] = Field(
        None, description="Sets privileged mode (--privileged) for the container."
    )
    securityOpt: Optional[List[str]] = Field(
        None,
        description="Sets container security options to include when creating the container.",
    )


class DevelopmentContainerFeatureMetadata(BaseModel):
    __root__: Feature = Field(
        ...,
        description="Development Container Features Metadata (devcontainer-feature.json). See https://containers.dev/implementors/features/ for more information.",
        title="Development Container Feature Metadata",
    )
