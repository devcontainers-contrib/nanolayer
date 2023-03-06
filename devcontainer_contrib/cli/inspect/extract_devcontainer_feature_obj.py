from devcontainer_contrib.utils.feature_oci import FeatureOCI
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_devcontainer_feature_obj(
    feature: str,
) -> Dict[str, Any]:
    return FeatureOCI(feature).get_devcontainer_feature_obj()
    