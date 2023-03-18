import os
import platform
import site
import sys
import tempfile
from pathlib import Path

import git
import invoke

from dcontainer.devcontainer.feature_generation.oci_feature_generator import \
    OCIFeatureGenerator
from dcontainer.devcontainer.models.devcontainer_feature import Mount
from dcontainer.devcontainer.models.devcontainer_feature_definition import (
    FeatureDefinition, TestScenario)


def execute_current_python_in_container(
     test_command: str, image: str, setup_command: str = "",
) -> bool:
    feature_definition = FeatureDefinition(id="test", version="0.0.0")
    mounts = []
    target_mounts_location = f"/mnt/{platform.node()}"

    for global_site_package in site.getsitepackages():
        mounts.append(
            Mount(
                source=global_site_package,
                target=os.path.join(
                    target_mounts_location, global_site_package.strip("/")
                ),
                type="bind",
            )
        )

    mounts.append(
        Mount(
            source=site.getusersitepackages(),
            target=os.path.join(
                target_mounts_location, site.getusersitepackages().strip("/")
            ),
            type="bind",
        )
    )

    repo = git.Repo(".", search_parent_directories=True)
    mounts.append(
        Mount(
            source=repo.working_tree_dir,
            target=os.path.join(
                target_mounts_location, repo.working_tree_dir.strip("/")
            ),
            type="bind",
        )
    )

    containerEnv = {
        "PYTHONPATH": f"{':'.join(mount.target for mount in mounts)}:$PYTHONPATH"
    }

    feature_definition.mounts = mounts
    feature_definition.containerEnv = containerEnv
    feature_definition.install_command = setup_command
    feature_definition.test_scenarios = [
        TestScenario(
            name="test_", test_commands=[test_command], image=image, options={}
        )
    ]

    with tempfile.TemporaryDirectory() as tempdir:
        feature_definition_obj_path = Path(tempdir, "feature-definition.json")
        with open(feature_definition_obj_path, "w") as f:
            f.write(feature_definition.json(indent=4))

        tmp_path_str = Path(tempdir, "generated_feature").as_posix()

        OCIFeatureGenerator.generate(
            feature_definition=feature_definition_obj_path,
            output_dir=tmp_path_str,
        )

        print(
            f"devcontainer features test -p {tmp_path_str} -f {feature_definition.id} --skip-autogenerated"
        )
        response = invoke.run(
            f"BUILDKIT_PROGRESS=plain devcontainer features test -p {tmp_path_str} -f {feature_definition.id} --skip-autogenerated",
            out_stream=sys.stdout,
            err_stream=sys.stderr,
            pty=True,
        )

        return response.return_code == 0




RESOURCE_DIR = os.path.join(os.path.dirname(__file__), "resources")
