from easyfs import Directory

from dcontainer.cli.generate.file_models.scenarios_json import ScenariosJson
from dcontainer.cli.generate.file_models.test_sh import TestSH
from dcontainer.models.devcontainer_feature_definition import (
    FeatureDefinition,
    TestScenario,
)


class TestDir(Directory):
    @classmethod
    def from_definition_model(cls, definition_model: FeatureDefinition) -> "Directory":
        feature_id = definition_model.id
        test_scenarios: TestScenario = definition_model.test_scenarios
        virtual_dir = {}
        virtual_dir[f"{feature_id}/scenarios.json"] = ScenariosJson(
            feature_id=feature_id, test_scenarios=test_scenarios
        )
        for test_scenario in test_scenarios:
            virtual_dir[f"{feature_id}/{test_scenario.name}.sh"] = TestSH(
                commands=test_scenario.test_commands
            )

        return cls(dictionary=virtual_dir)
