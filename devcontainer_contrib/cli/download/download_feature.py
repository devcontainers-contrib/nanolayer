import logging
import os

from devcontainer_contrib.utils.oci_feature import OCIFeature

logger = logging.getLogger(__name__)


def download_feature(
    feature: str,
) -> str:
    return OCIFeature(feature).download(os.getcwd())
