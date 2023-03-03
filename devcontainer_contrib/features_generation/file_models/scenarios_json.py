from typing import List
from devcontainer_contrib.models.devcontainer_feature_definition import TestScenario
from easyfs import File
import json


class ScenariosJson(File):
    def __init__(self, feature_id: str, test_scenarios: List[TestScenario]) -> None:
        scenarios = {}
        for test_scenario in test_scenarios:
            scenarios[test_scenario.name] = {
                "image": test_scenario.image,
                "features": {feature_id: test_scenario.options or {}},
            }

        super().__init__(json.dumps(scenarios, indent=4).encode())
