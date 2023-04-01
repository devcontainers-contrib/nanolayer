import os
import tempfile
from pathlib import Path
from typing import Union

from nanolayer.installers.devcontainer_feature.models.devcontainer_feature import (
    Feature,
)
from nanolayer.utils.oci_registry import OCIRegistry


class OCIFeature:
    DEVCONTAINER_JSON_FILENAME = "devcontainer-feature.json"
    DEVCONTAINER_FILE_NAME_ANNOTATION = "org.opencontainers.image.title"

    @staticmethod
    def download(oci_feature_ref: str, output_dir: Union[str, Path]) -> str:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir.is_file():
            raise ValueError("output_dir is a file")

        output_dir.parent.mkdir(parents=True, exist_ok=True)

        manifest = OCIRegistry.get_manifest(oci_feature_ref)

        assert len(manifest["layers"]) == 1, "feature oci should have 1 layer only"

        file_name = manifest["layers"][0]["annotations"][
            OCIFeature.DEVCONTAINER_FILE_NAME_ANNOTATION
        ]

        file_location = output_dir.joinpath(file_name)

        OCIRegistry.download_layer(
            oci_input=oci_feature_ref,
            layer_num=0,
            output_file=file_location,
        )

        return file_location.as_posix()

    @staticmethod
    def download_and_extract(
        oci_feature_ref: str, output_dir: Union[str, Path]
    ) -> None:
        OCIRegistry.download_and_extract_layer(
            oci_input=oci_feature_ref, layer_num=0, output_dir=output_dir
        )

    @staticmethod
    def get_devcontainer_feature_obj(oci_feature_ref: str) -> Feature:
        with tempfile.TemporaryDirectory() as extraction_dir:
            OCIFeature.download_and_extract(
                oci_feature_ref=oci_feature_ref, output_dir=extraction_dir
            )

            return Feature.parse_file(
                os.path.join(extraction_dir, OCIFeature.DEVCONTAINER_JSON_FILENAME)
            )
