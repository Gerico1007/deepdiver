from pathlib import Path

import tomllib
from click.testing import CliRunner

from deepdiver import __version__
from deepdiver.deepdive import cli


def _pyproject_version() -> str:
    data = tomllib.loads(Path("pyproject.toml").read_text())
    return data["project"]["version"]


def test_package_version_matches_pyproject():
    assert __version__ == _pyproject_version()


def test_cli_version_output_matches_package_version():
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
