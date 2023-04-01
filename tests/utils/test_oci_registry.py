import pathlib

import pytest

from minilayer.utils.oci_registry import OCIRegistry

TEST_OCI_OBJECT = "ghcr.io/devcontainers-contrib/features/bash-command:1.0.0"


@pytest.mark.parametrize(
    "oci_ref",
    [TEST_OCI_OBJECT],
)
def test_oci_registry_get_manifest(shell, tmp_path: pathlib.Path, oci_ref: str) -> None:
    manifest = OCIRegistry.get_manifest(oci_ref)
    print(manifest)
    assert isinstance(manifest, dict)


@pytest.mark.parametrize(
    "oci_ref",
    [TEST_OCI_OBJECT],
)
def test_oci_registry_download_layer(
    shell, tmp_path: pathlib.Path, oci_ref: str
) -> None:
    output_location = tmp_path.joinpath("layer.tgz")
    assert not output_location.exists()
    OCIRegistry.download_layer(
        oci_input=oci_ref, layer_num=0, output_file=output_location
    )
    assert output_location.exists()


@pytest.mark.parametrize(
    "oci_ref",
    [TEST_OCI_OBJECT],
)
def test_oci_registry_download_and_extract_layer(
    shell, tmp_path: pathlib.Path, oci_ref: str
) -> None:
    output_location = tmp_path.joinpath("somedir")
    assert not output_location.exists()
    OCIRegistry.download_and_extract_layer(
        oci_input=oci_ref, layer_num=0, output_dir=output_location
    )
    assert output_location.exists()
    assert len(list(output_location.iterdir())) == 2
