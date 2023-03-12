import logging
from typing import Dict, Optional

from dcontainer.oci.oci_feature import OCIFeature
from dcontainer.oci.oci_feature_installer import OCIFeatureInstaller

logger = logging.getLogger(__name__)


def install_feature(
    feature: str,
    options: Optional[Dict[str, str]] = None,
    remote_user: Optional[str] = None,
    verbose: bool = False,
) -> None:
    OCIFeatureInstaller.install(OCIFeature(feature), options, remote_user, verbose)
