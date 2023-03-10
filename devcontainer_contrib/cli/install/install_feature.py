from typing import Dict, Optional
import logging

from devcontainer_contrib.utils.feature_oci import FeatureOCI
from devcontainer_contrib.utils.feature_oci_installer import FeatureOCIInstaller

logger = logging.getLogger(__name__)


def install_feature(
    feature: str,
    options: Optional[Dict[str, str]] = None,
    remote_user: Optional[str] = None
) -> None:
    FeatureOCIInstaller.install(FeatureOCI(feature), options, remote_user )
  