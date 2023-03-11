import logging
from typing import Dict, Optional

from devcontainer_contrib.utils.oci_feature import OCIFeature
from devcontainer_contrib.utils.oci_feature_installer import OCIFeatureInstaller

logger = logging.getLogger(__name__)


def install_feature(
    feature: str,
    options: Optional[Dict[str, str]] = None,
    remote_user: Optional[str] = None,
    verbose: bool = False
) -> None:
    OCIFeatureInstaller.install(OCIFeature(feature), options, remote_user, verbose)
