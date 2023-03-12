import logging
import os

from dcontainer.oci.oci_feature import OCIFeature

logger = logging.getLogger(__name__)


def download_feature(
    feature: str,
) -> str:
    return OCIFeature(feature).download(os.getcwd())
