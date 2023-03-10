import os
from devcontainer_contrib.utils.oci_feature import OCIFeature

import logging
logger = logging.getLogger(__name__)


def download_feature(
    feature: str,
) -> None:
    return OCIFeature(feature).download(os.getcwd())
