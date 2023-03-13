import logging
from typing import Dict, Optional

from dcontainer.oci.oci_feature import OCIFeature
from dcontainer.oci.oci_feature_installer import OCIFeatureInstaller

logger = logging.getLogger(__name__)


def install_feature(
    feature: str,
    options: Optional[Dict[str, str]] = None,
    envs: Optional[Dict[str, str]] = None,
    remote_user: Optional[str] = None,
    verbose: bool = False,
) -> None:
    OCIFeatureInstaller.install(feature_oci=OCIFeature(feature), envs=envs, options=options, remote_user=remote_user, verbose=verbose)
