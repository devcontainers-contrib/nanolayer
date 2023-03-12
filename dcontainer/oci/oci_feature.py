import os
import tarfile
import tempfile
from pathlib import Path
from typing import Union

from dcontainer.models.devcontainer_feature import Feature
from dcontainer.oci.oci_registry import OCIRegistry


class OCIFeature:
    PATH_REGEX = r"/^[a-z0-9]+([._-][a-z0-9]+)*(\/[a-z0-9]+([._-][a-z0-9]+)*)*$/"
    regexForPath = r"/^[a-z0-9]+([._-][a-z0-9]+)*(\/[a-z0-9]+([._-][a-z0-9]+)*)*$/"

    def __init__(self, oci_feature_ref: str) -> None:
        self.oci_feature_ref = oci_feature_ref

    def download(self, output_dir: Union[str, Path]) -> str:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir.is_file():
            raise ValueError("output_dir is a file")

        output_dir.parent.mkdir(parents=True, exist_ok=True)

        manifest = OCIRegistry.get_manifest(self.oci_feature_ref)

        assert len(manifest["layers"]) == 1, "feature oci should have 1 layer only"

        blob_digest = manifest["layers"][0]["digest"]
        file_name = manifest["layers"][0]["annotations"][
            "org.opencontainers.image.title"
        ]

        file_location = output_dir.joinpath(file_name)
        with open(file_location, "wb") as f:
            f.write(OCIRegistry.get_blob(self.oci_feature_ref, blob_digest))

        return file_location.as_posix()

    def download_and_extract(self, output_dir: Union[str, Path]) -> None:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file (should be an empty directory)")

        if any(output_dir.iterdir()):
            raise ValueError(f"{output_dir} is not empty ")

        with tempfile.TemporaryDirectory() as download_dir:
            feature_targz_location = self.download(download_dir)
            with tarfile.open(feature_targz_location, "r") as tar:
                tar.extractall(output_dir)

    def get_devcontainer_feature_obj(self) -> Feature:
        with tempfile.TemporaryDirectory() as extraction_dir:
            self.download_and_extract(extraction_dir)

            return Feature.parse_file(
                os.path.join(extraction_dir, "devcontainer-feature.json")
            )
