from devcontainer_contrib.utils.feature_oci import FeatureOCI
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_devcontainer_feature_dict(
    feature: str,
) -> Dict[str, Any]:
    feature_definition = FeatureOCI(feature).get_devcontainer_feature_obj()

    return feature_definition.dict(exclude_none=True)
    