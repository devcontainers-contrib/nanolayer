import pathlib
import re

from pkg_resources import parse_requirements
from setuptools import find_packages, setup


def fix_requirement_line(line: str) -> str:
    if line.startswith("git+"):
        egg_name = re.search(r"egg=([a-zA-Z_\-0-9\s]+)", line).group(1)
        return f"{egg_name.strip()} @ {line}"
    return line


with open("requirements.txt", "r") as f:
    REQUIREMENTS = [
        str(requirement)
        for requirement in parse_requirements(
            [fix_requirement_line(line) for line in f.readlines()]
        )
    ]


with open("requirements-dev.txt", "r") as f:
    REQUIREMENTS_DEV = [
        str(requirement)
        for requirement in parse_requirements(
            [fix_requirement_line(line) for line in f.readlines()]
        )
    ]


setup(
    name="nanolayer",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Daniel Braun",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    package_data={"nanolayer": ["py.typed"]},
    long_description_content_type="text/markdown",
    long_description=(pathlib.Path(__file__).parent.resolve() / "README.md").read_text(
        encoding="utf-8"
    ),
    extras_require={
        "dev": REQUIREMENTS_DEV,
    },
    entry_points={"console_scripts": ["nanolayer=nanolayer.__main__:main"]},
)
