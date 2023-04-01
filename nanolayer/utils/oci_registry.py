import hashlib
import http.client
import json
import re
import tarfile
import tempfile
import urllib
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class OCIRegistry:
    class HashException(Exception):
        pass

    ACCEPT_HEADER = {
        "Accept": ", ".join(
            (
                "application/vnd.docker.distribution.manifest.v1+json",
                "application/vnd.docker.distribution.manifest.v2+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.oci.image.manifest.v1+json",
                "application/vnd.oci.image.index.v1+json",
            )
        )
    }

    class WWWAthenticate(BaseModel):
        realm: str
        service: str
        scope: str

    class ParsedOCIRef(BaseModel):
        _id: str
        version: str
        owner: str
        namespace: str
        registry: str
        resource: str
        path: str

    WWW_AUTHENTICATE_REGEX = r'.*[Ww]ww-[Aa]uthenticate:\sBearer\srealm="([\w:/\.]+)",service="([\w:/\.]+)",scope="([\w:/\-,]+)".*'

    @staticmethod
    def parse_oci(oci_input: str) -> "OCIRegistry.ParsedOCIRef":
        """
        following code was adapted from:
        https://github.com/devcontainers/cli/blob/a1bf89bdef26a9ebfee5dbd0ed60b008e636de18/src/spec-configuration/containerCollectionsOCI.ts#L83
        """
        oci_input = oci_input.replace("http://", "")
        oci_input = oci_input.replace("https://", "")

        index_of_last_colon = oci_input.rfind(":")

        if index_of_last_colon == -1 or index_of_last_colon < oci_input.index("/"):
            resource = oci_input
            version = "latest"
        else:
            resource = oci_input[:index_of_last_colon]
            version = oci_input[index_of_last_colon + 1 :]

        split_on_slash = resource.split("/")

        _id = split_on_slash[-1]
        owner = split_on_slash[1]
        registry = split_on_slash[0]
        namespace = "/".join(split_on_slash[1:-1])
        path = f"{namespace}/{_id}"

        return OCIRegistry.ParsedOCIRef(
            _id=_id,
            version=version,
            owner=owner,
            namespace=namespace,
            registry=registry,
            resource=resource,
            path=path,
        )

    @staticmethod
    def _parse_www_authenticate(
        response_headers: Union[str, List[str], Dict[str, str]]
    ) -> WWWAthenticate:
        if isinstance(response_headers, str):
            response_headers = response_headers.splitlines()

        elif isinstance(response_headers, dict):
            response_headers = [
                f"{key}: {value}" for key, value in response_headers.items()
            ]

        for line in response_headers:
            result = re.match(OCIRegistry.WWW_AUTHENTICATE_REGEX, line)
            if result is None:
                continue
            return OCIRegistry.WWWAthenticate(
                realm=result.group(1), service=result.group(2), scope=result.group(3)
            )
        raise ValueError(
            f"failed to parse www-authenticate from the given string: {str(response_headers)}"
        )

    @staticmethod
    def _generate_token(raw_response_header: str) -> str:
        www_authenticate = OCIRegistry._parse_www_authenticate(raw_response_header)

        token_request_link = f"{www_authenticate.realm}?service={www_authenticate.service}&scope={www_authenticate.scope}"
        if not token_request_link.startswith("http"):
            raise ValueError("only http/https links are permited")

        response = urllib.request.urlopen(token_request_link)  # nosec
        token = json.loads(response.read())["token"]
        return token

    @staticmethod
    def _attempt_request(
        url: str, headers: Optional[Dict[str, str]] = None
    ) -> http.client.HTTPResponse:
        if not url.startswith("http"):
            raise ValueError("only http/https links are permited")

        if headers is None:
            headers = {}

        if "User-Agent" not in headers:
            headers["User-Agent"] = "nanolayer"

        request = urllib.request.Request(url=url, headers=headers)

        try:
            response = urllib.request.urlopen(request)  # nosec
            return response

        except urllib.error.HTTPError as e:
            token = OCIRegistry._generate_token(e.headers.as_string())
            request.add_header("Authorization", f"Bearer {token}")
            return urllib.request.urlopen(request)  # nosec

    @staticmethod
    def download_layer(
        oci_input: str, layer_num: int, output_file: Union[str, Path]
    ) -> None:
        if isinstance(output_file, str):
            output_file = Path(output_file)

        if output_file.exists():
            raise ValueError(f"{output_file.as_posix()} already exists")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        manifest = OCIRegistry.get_manifest(oci_input)

        blob_digest = manifest["layers"][layer_num]["digest"]

        with open(output_file, "wb") as f:
            f.write(OCIRegistry.get_blob(oci_input, blob_digest))

    @staticmethod
    def download_and_extract_layer(
        oci_input: str, output_dir: Union[str, Path], layer_num: int
    ) -> None:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file (should be an empty directory)")

        output_dir.mkdir(parents=True, exist_ok=True)

        if any(output_dir.iterdir()):
            raise ValueError(f"{output_dir} is not empty ")

        with tempfile.TemporaryDirectory() as download_dir:
            layer_file = Path(download_dir).joinpath("layer_file.tgz")
            OCIRegistry.download_layer(
                oci_input=oci_input, layer_num=layer_num, output_file=layer_file
            )
            with tarfile.open(layer_file, "r") as tar:
                tar.extractall(output_dir)

    @staticmethod
    def get_manifest(oci_input: str) -> Dict[str, Any]:
        parsed_oci = OCIRegistry.parse_oci(oci_input=oci_input)
        url = f"https://{parsed_oci.registry}/v2/{parsed_oci.path}/manifests/{parsed_oci.version}"
        response = OCIRegistry._attempt_request(url, headers=OCIRegistry.ACCEPT_HEADER)
        return json.loads(response.read().decode())

    @staticmethod
    def get_blob(oci_input: str, digest: str) -> bytes:
        parsed_oci = OCIRegistry.parse_oci(oci_input=oci_input)
        url = f"https://{parsed_oci.registry}/v2/{parsed_oci.path}/blobs/{digest}"
        response = OCIRegistry._attempt_request(url)
        blob = response.read()

        calculated_digest = f"sha256:{hashlib.sha256(blob).hexdigest()}"
        if not calculated_digest == digest:
            raise OCIRegistry.HashException(
                f"bad calculated digest: {calculated_digest} (expected {digest})"
            )

        return blob
