import os
from devcontainer_contrib.utils.feature_oci import FeatureOCI

import logging
logger = logging.getLogger(__name__)


def download_feature(
    feature: str,
) -> None:
    return FeatureOCI(feature).download(os.getcwd())
