from setuptools import setup, find_packages
import pathlib
from pkg_resources import parse_requirements
import re

here = pathlib.Path(__file__).parent.resolve()


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


with open("requirements-generate.txt", "r") as f:
    REQUIREMENTS_GENERATE = [
        str(requirement)
        for requirement in parse_requirements(
            [fix_requirement_line(line) for line in f.readlines()]
        )
    ]


setup(
    name="minilayer",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="Daniel Braun",
    packages=find_packages(),
    install_requires=REQUIREMENTS,

    extras_require={ 
            "dev": REQUIREMENTS_DEV,
            "generate": REQUIREMENTS_GENERATE,
        },

    entry_points = {
        'console_scripts': ['minilayer=minilayer.__main__:main']
    }
)

