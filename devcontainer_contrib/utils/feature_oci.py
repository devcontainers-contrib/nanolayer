import dxf
from typing import Union, cast
from pathlib import Path
import json 
import tempfile
import tarfile
import os
from devcontainer_contrib.models.devcontainer_feature import Feature


class FeatureOCI:
    PATH_REGEX = r"/^[a-z0-9]+([._-][a-z0-9]+)*(\/[a-z0-9]+([._-][a-z0-9]+)*)*$/"
    regexForPath = r"/^[a-z0-9]+([._-][a-z0-9]+)*(\/[a-z0-9]+([._-][a-z0-9]+)*)*$/"


    @staticmethod
    def parse_oci(oci_input: str):
        """
        following code was adapted from:
        https://github.com/devcontainers/cli/blob/a1bf89bdef26a9ebfee5dbd0ed60b008e636de18/src/spec-configuration/containerCollectionsOCI.ts#L83
        """
        index_of_last_colon = oci_input.rfind(":")
        
        if index_of_last_colon == -1 or index_of_last_colon < oci_input.index('/'):
            resource = oci_input
            version = "latest"
        else:
            resource = oci_input[:index_of_last_colon]
            version = oci_input[index_of_last_colon + 1 :]
        
        split_on_slash = resource.split("/")

        _id = split_on_slash[-1]
        owner = split_on_slash[1]
        registry = split_on_slash[0]
        namespace = '/'.join(split_on_slash[1:-1])
        path = f"{namespace}/{_id}"

        return (_id,
                version,
                owner,
                namespace,
                registry,
                resource,
                path)
    

    def __init__(self, path: str) -> None:
        self._id, self.version,self.owner,self.namespace,self.registry,self.resource,self.path = FeatureOCI.parse_oci(path)    

    def download(self, output_dir: Union[str, Path]) -> str:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir.is_file():
            raise ValueError("output_dir is a file")
            
        output_dir.parent.mkdir(parents=True, exist_ok=True)

        repo_handler = dxf.DXF(self.registry, self.path)
        repo_handler.authenticate(actions=["pull"])

        manifest = json.loads(repo_handler.get_manifest(self.version))
        assert len(manifest['layers']) == 1, "feature oci should have 1 layer only"

        blob_digest = manifest['layers'][0]['digest']
        file_name = manifest['layers'][0]['annotations']['org.opencontainers.image.title']

        file_location = output_dir.joinpath(file_name)
        with open(file_location, "wb") as f:
            for bytes_chunk in repo_handler.pull_blob(blob_digest):
                f.write(cast(bytes, bytes_chunk))
        
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

    def get_devcontainer_feature_obj(self)-> Feature:

        with tempfile.TemporaryDirectory() as extraction_dir:
            self.download_and_extract(extraction_dir)

            return Feature.parse_file(os.path.join(extraction_dir, "devcontainer-feature.json"))
