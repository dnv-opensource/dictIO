import logging
import os
from pathlib import Path
from shutil import rmtree

import pytest


@pytest.fixture(scope="package", autouse=True)
def chdir() -> None:
    os.chdir(Path(__file__).parent.absolute() / "test_dicts")


@pytest.fixture(scope="package", autouse=True)
def test_dir() -> Path:
    return Path(__file__).parent.absolute()


output_dirs: list[str] = []
output_files: list[str] = [
    "parsed.*",
]


@pytest.fixture(autouse=True)
def default_setup_and_teardown():
    _remove_output_dirs_and_files()
    yield
    _remove_output_dirs_and_files()


def _remove_output_dirs_and_files() -> None:
    for folder in output_dirs:
        rmtree(folder, ignore_errors=True)
    for pattern in output_files:
        for file in Path.cwd().glob(pattern):
            _file = Path(file)
            _file.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    caplog.clear()


@pytest.fixture(autouse=True)
def logger() -> logging.Logger:
    return logging.getLogger()
