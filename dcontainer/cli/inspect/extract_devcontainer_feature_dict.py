import logging
from typing import Any, Dict

from dcontainer.oci.oci_feature import OCIFeature

logger = logging.getLogger(__name__)


def extract_devcontainer_feature_dict(
    feature: str,
) -> Dict[str, Any]:
    feature_definition = OCIFeature(feature).get_devcontainer_feature_obj()

    return feature_definition.dict(exclude_none=True)
